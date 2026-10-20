import unittest

from scripts.fetch_company_icons import icon_candidates, image_extension


class CompanyIconTests(unittest.TestCase):
    def test_prefers_apple_and_largest_declared_size(self):
        html = '''<link rel="icon" href="favicon.ico">
        <link rel="apple-touch-icon" href="small.png" sizes="120x120">
        <link rel="apple-touch-icon-precomposed" href="large.png" sizes="180x180">'''
        icons = icon_candidates(html, "https://example.com/product/")
        self.assertEqual(icons[0].url, "https://example.com/product/large.png")
        self.assertEqual(icons[0].kind, "apple-touch-icon")
        self.assertLess(next(i for i, icon in enumerate(icons) if icon.url.endswith("apple-touch-icon.png")), next(i for i, icon in enumerate(icons) if icon.url.endswith("favicon.ico")))

    def test_handles_base_url_and_duplicate_relations(self):
        html = '''<base href="https://cdn.example.com/assets/">
        <link rel="shortcut icon" href="icon.png">
        <link rel="icon" href="icon.png">'''
        icons = icon_candidates(html, "https://example.com/")
        self.assertEqual(sum(icon.url == "https://cdn.example.com/assets/icon.png" for icon in icons), 1)

    def test_rejects_non_http_links_and_unrelated_metadata(self):
        html = '''<link rel="icon" href="javascript:alert(1)">
        <link rel="preload" href="tracker.png">'''
        self.assertEqual([icon.url for icon in icon_candidates(html, "https://example.com/")], ["https://example.com/apple-touch-icon.png", "https://example.com/favicon.ico"])

    def test_checks_image_bytes_and_rejects_html_error_pages(self):
        self.assertEqual(image_extension(b"\x89PNG\r\n\x1a\nrest"), "png")
        self.assertEqual(image_extension(b"\x00\x00\x01\x00rest"), "ico")
        self.assertIsNone(image_extension(b"<!DOCTYPE html><html>404</html>"))

    def test_accepts_static_svg_and_rejects_active_content(self):
        self.assertEqual(image_extension(b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>'), "svg")
        self.assertIsNone(image_extension(b'<svg onload="alert(1)"/>'))
        self.assertIsNone(image_extension(b'<svg><script>alert(1)</script></svg>'))
        self.assertIsNone(image_extension(b'<svg><use href="https://example.com/external.svg"/></svg>'))


if __name__ == "__main__":
    unittest.main()
