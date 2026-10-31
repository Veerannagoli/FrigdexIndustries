# Frigdex Industries SEO implementation

## Included in this update

- `/robots.txt` route: permits public crawling and excludes `/admin` paths.
- `/sitemap.xml` route: lists the four public pages and every active product detail URL.
- Canonical URLs using `https://frigdex.in`.
- Page title and meta description output from each template's SEO blocks.
- Open Graph and Twitter sharing metadata.
- LocalBusiness structured data with the public business address already shown on the website.
- Product structured data on individual product detail pages.
- The actual Frigdex logo is used as the favicon and Apple touch icon.

## After deploying

1. Push the updated project to GitHub and let Render deploy it.
2. Check `https://frigdex.in/robots.txt`.
3. Check `https://frigdex.in/sitemap.xml`. It should include active product pages as well as the main pages.
4. In Google Search Console, open Sitemaps and confirm `https://frigdex.in/sitemap.xml` is still successful.
5. Use URL Inspection for any newly added product pages and request indexing if needed.

## Important

- Keep `.env` private. It is intentionally not included in this ZIP. Use your existing local `.env` and Render environment variables; `.env.example` is included as a reference.
- Do not add admin pages, login pages, enquiry URLs or filtered product search URLs to the sitemap.
- Search engines decide when to crawl and index pages. Sitemap submission does not guarantee rankings.
