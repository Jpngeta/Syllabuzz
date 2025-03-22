from services.arXiv_service import ArxivService

service = ArxivService()
papers = service.fetch_papers("cs.AI", max_results=5)
print(f"Found {len(papers)} papers:")
for paper in papers:
    print(f"- {paper['title']}")