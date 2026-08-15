import asyncio
from typing import Dict, Any, List
from playwright.async_api import async_playwright
from app.agents.base import BaseAgent, AgentResponse

class BrowserAgent(BaseAgent):
    """
    Agent responsible for browsing the web, extracting text, and automating web tasks.
    Uses Playwright for headless/headed browser control.
    """
    def __init__(self):
        super().__init__(name="BrowserAgent", description="Navigates websites and extracts data.")
        self.playwright = None
        self.browser = None
        self.page = None

    async def _init_browser(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()

    async def process_request(self, request: str, context: Dict[str, Any] = None) -> AgentResponse:
        req_lower = request.lower()
        
        # Super simple intent matching for the sake of architecture
        if "go to" in req_lower or "open url" in req_lower:
            url = self._extract_url(request)
            if url:
                await self._init_browser()
                await self.page.goto(url)
                title = await self.page.title()
                return AgentResponse(
                    status="success",
                    message=f"Navigated to {url}. Page title: {title}",
                    data={"url": url, "title": title}
                )
            return AgentResponse(status="error", message="Could not find a valid URL in the request.")
            
        elif "extract text" in req_lower or "read page" in req_lower:
            await self._init_browser()
            text = await self.page.evaluate("() => document.body.innerText")
            # Truncate text for safety
            return AgentResponse(
                status="success",
                message="Successfully extracted text from the page.",
                data={"text": text[:1000]} 
            )

        return AgentResponse(status="unknown", message="Command not recognized by BrowserAgent.")

    def _extract_url(self, request: str) -> str:
        words = request.split()
        for word in words:
            if word.startswith("http") or "www." in word or ".com" in word:
                if not word.startswith("http"):
                    return f"https://{word}"
                return word
        return ""

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
