"""Regression checks for the actual TeX export patterns that broke PDF links."""
from pathlib import Path
import sys
import unittest
from io import BytesIO

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_links import repair_links
from validate_pdf_links import audit_pdf


class PDFLinkTests(unittest.TestCase):
    def fixture(self):
        sources = {
            'authoring': '---\ntitle: 6. Authoring\n---\n## 6.1 Metadata\n## 6.2 State\n',
            'review': '---\ntitle: 10. Review\n---\n(anchor)=\n## 10.2 Review\n',
            'checklist': '---\ntitle: 14. Checklist\n---\n[第 6.2 节](authoring.md)\n[第 10.2 节](#anchor)\n',
        }
        tex = {
            'authoring': '\\chapter{Authoring}\n\\section{Metadata}\n\\section{State}\n',
            'review': '\\chapter{Review}\n\\section{Review}\\label{anchor}\n',
            'checklist': '\\chapter{Checklist}\n\\href{/authoring}{第 6.2 节}\n第~10.2~节\n',
        }
        return sources, tex

    def test_real_export_patterns_become_section_links(self):
        sources, tex = self.fixture()
        fixed, links = repair_links(sources, tex)
        self.assertNotIn('\\href{/authoring}', fixed['checklist'])
        self.assertIn('\\hyperref[hs-authoring-s2]{第 6.2 节}', fixed['checklist'])
        self.assertIn('\\hyperref[hs-review-s1]{第~10.2~节}', fixed['checklist'])
        self.assertIn('\\section{State}\\label{hs-authoring-s2}', fixed['authoring'])
        self.assertEqual(len(links), 2)

    def test_external_links_and_literal_examples_are_unchanged(self):
        sources, tex = self.fixture()
        literal = '\\begin{lstlisting}\n\\href{/fake}{code}\n\\end{lstlisting}'
        tex['checklist'] += '\\href{https://example.com}{External}\n' + literal
        fixed, _ = repair_links(sources, tex)
        self.assertIn('\\href{https://example.com}{External}', fixed['checklist'])
        self.assertIn(literal, fixed['checklist'])

    def test_unknown_chapter_fails_closed(self):
        sources, tex = self.fixture()
        tex['checklist'] += '\\href{/missing}{Missing}'
        with self.assertRaisesRegex(ValueError, 'unknown PDF chapter'):
            repair_links(sources, tex)

    def test_unknown_section_fails_closed(self):
        sources, tex = self.fixture()
        tex['checklist'] = tex['checklist'].replace('6.2', '6.8')
        with self.assertRaisesRegex(ValueError, 'unknown section'):
            repair_links(sources, tex)

    def test_missing_heading_fails_closed(self):
        sources, tex = self.fixture()
        tex['authoring'] = tex['authoring'].replace('\\section{State}', '')
        with self.assertRaisesRegex(ValueError, 'heading count'):
            repair_links(sources, tex)

    def test_lost_explicit_reference_fails_closed(self):
        sources, tex = self.fixture()
        tex['checklist'] = tex['checklist'].replace('第~10.2~节', '')
        with self.assertRaisesRegex(ValueError, 'reference count'):
            repair_links(sources, tex)

    def test_range_lands_at_first_section_and_formatted_text_survives(self):
        sources, tex = self.fixture()
        tex['checklist'] = tex['checklist'].replace('第 6.2 节', '第 6.1---6.2 节')
        tex['checklist'] += '\\href{/authoring}{\\textbf{Metadata}}'
        fixed, _ = repair_links(sources, tex)
        self.assertIn('\\hyperref[hs-authoring-s1]{第 6.1---6.2 节}', fixed['checklist'])
        self.assertIn('\\hyperref[hs-authoring]{\\textbf{Metadata}}', fixed['checklist'])


class PDFArtifactTests(unittest.TestCase):
    def pdf(self, action='/GoTo', destination='section.1', include_link=True, x=20):
        from pypdf import PdfWriter
        from pypdf.generic import ArrayObject, NameObject, NumberObject, TextStringObject
        writer = PdfWriter()
        page = writer.add_blank_page(200, 200)
        for name, y in [('hs-link-1', 100), ('section.1', 180), ('section.2', 150)]:
            writer.add_named_destination_array(TextStringObject(name), ArrayObject([
                page.indirect_reference, NameObject('/XYZ'), NumberObject(20), NumberObject(y), NumberObject(0)]))
        if include_link:
            data = {'/S': action, '/D': destination}
            if action == '/GoToR':
                data['/F'] = '/authoring.pdf'
            writer.add_annotation(page, {'/Type': '/Annot', '/Subtype': '/Link',
                                        '/Rect': [x, 95, x+50, 108], '/A': data})
        stream = BytesIO()
        writer.write(stream)
        stream.seek(0)
        return stream

    @property
    def expected(self):
        return [{'source': 'hs-link-1', 'target': 'hs-label', 'destination': 'section.1'}]

    def test_actual_pdf_internal_link_passes(self):
        self.assertEqual(audit_pdf(self.pdf(), self.expected)['verified_body_links'], 1)

    def test_external_file_action_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'forbidden link action /GoToR'):
            audit_pdf(self.pdf(action='/GoToR'), self.expected)

    def test_missing_clickable_area_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no clickable link'):
            audit_pdf(self.pdf(include_link=False), self.expected)

    def test_wrong_destination_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no clickable link'):
            audit_pdf(self.pdf(destination='section.2'), self.expected)

    def test_unrelated_clickable_area_on_same_page_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no clickable link'):
            audit_pdf(self.pdf(x=120), self.expected)

    def test_undefined_destination_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unresolved destination'):
            audit_pdf(self.pdf(destination='missing'), self.expected)

    def test_incomplete_manifest_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source markers differ'):
            audit_pdf(self.pdf(), [])


if __name__ == '__main__':
    unittest.main()
