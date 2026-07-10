"""
Text cleaning and normalization for mining documents.

Handles:
- HTML residue removal
- Whitespace normalization
- Chinese text normalization
- Content quality filtering (too short / boilerplate)
"""

import re
from typing import List, Optional

from loguru import logger

from .config import MiningDocument


class TextCleaner:
    """Clean and normalize document content."""

    # Patterns to remove
    HTML_TAG_RE = re.compile(r"<[^>]+>")
    MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
    MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
    URL_RE = re.compile(r"https?://\S+")
    SHARE_RE = re.compile(
        r"(Share\s*this|Share\s*on|Tweet|Facebook|LinkedIn|WeChat|微信|分享到)",
        re.IGNORECASE,
    )
    COOKIE_RE = re.compile(
        r"(cookie|cookies|隐私|privacy|accept all|accept cookies)",
        re.IGNORECASE,
    )

    # Chinese-specific cleaning
    CHINESE_PUNCT_RE = re.compile(r"[　]")  # Full-width space → normal space
    CHINESE_BOILERPLATE = re.compile(
        r"(版权所有|免责声明|网站地图|关于我们|联系我们|京ICP备|粤ICP备)",
    )

    MIN_CONTENT_LENGTH = 50  # Minimum characters for valid content
    MIN_CONTENT_LENGTH_ZH = 30  # Chinese text is more compact

    @classmethod
    def clean(cls, docs: List[MiningDocument]) -> List[MiningDocument]:
        """Clean a batch of documents. Returns only valid ones."""
        cleaned = []
        for doc in docs:
            try:
                cleaned_doc = cls._clean_one(doc)
                if cleaned_doc and cls._is_valid(cleaned_doc):
                    cleaned.append(cleaned_doc)
                else:
                    logger.debug(f"Dropped invalid doc: {doc.title[:80]}")
            except Exception as e:
                logger.warning(f"Error cleaning doc '{doc.title[:80]}': {e}")

        logger.info(
            f"Cleaning: {len(docs)} → {len(cleaned)} documents "
            f"({len(docs) - len(cleaned)} dropped)"
        )
        return cleaned

    @classmethod
    def _clean_one(cls, doc: MiningDocument) -> Optional[MiningDocument]:
        """Clean a single document."""
        content = doc.content
        title = doc.title

        # Remove HTML tags
        content = cls.HTML_TAG_RE.sub(" ", content)

        # Remove URLs (keep the text context)
        content = cls.URL_RE.sub(" ", content)

        # Remove share / social media boilerplate
        content = cls.SHARE_RE.sub(" ", content)
        content = cls.COOKIE_RE.sub(" ", content)

        # Normalize Chinese full-width spaces
        content = cls.CHINESE_PUNCT_RE.sub(" ", content)

        # Collapse whitespace
        content = cls.MULTI_SPACE_RE.sub(" ", content)
        content = cls.MULTI_NEWLINE_RE.sub("\n\n", content)

        # Strip leading/trailing boilerplate lines
        lines = content.split("\n")
        lines = [
            line.strip()
            for line in lines
            if line.strip() and not cls.CHINESE_BOILERPLATE.search(line)
        ]
        content = "\n".join(lines)

        # Clean title
        title = title.strip()
        title = cls.HTML_TAG_RE.sub("", title)

        # Create cleaned document
        return MiningDocument(
            id=doc.id,
            source=doc.source,
            category=doc.category,
            title=title,
            content=content.strip(),
            url=doc.url,
            published_at=doc.published_at,
            language=doc.language,
            metadata=doc.metadata,
            ingested_at=doc.ingested_at,
        )

    @classmethod
    def _is_valid(cls, doc: MiningDocument) -> bool:
        """Check if document has sufficient quality content."""
        content_len = len(doc.content)
        min_len = (
            cls.MIN_CONTENT_LENGTH_ZH
            if doc.language == "zh"
            else cls.MIN_CONTENT_LENGTH
        )

        if content_len < min_len:
            return False

        # Check for mostly-boilerplate content
        boilerplate_indicators = [
            "javascript",
            "enable javascript",
            "请启用javascript",
            "请开启JavaScript",
        ]
        content_lower = doc.content.lower()
        if any(bp in content_lower for bp in boilerplate_indicators):
            return False

        return True
