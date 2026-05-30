"""
adviser/ingestion/vision.py
VisionRAG: Layout-aware page-level document indexing and visual embeddings using ColPali.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, List

from rich.console import Console

console = Console(stderr=True)


class VisionRAGIndexer:
    """
    Visual document indexer using page-level image embeddings (ColPali).
    Converts PDF pages into high-DPI image tensors and embeds their visual layout
    to capture tables, grids, and diagrams accurately.
    """

    def __init__(
        self, model_id: str = "vidore/colpali-v1.2", cache_dir: Optional[Path] = None
    ) -> None:
        self.model_id = model_id
        self._model: Any = None
        self._processor: Any = None
        self.cache_dir = cache_dir or Path.home() / ".local" / "share" / "adviser" / "vision_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect acceleration device
        self.device = "cpu"
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
        except ImportError:
            pass

    def load_model(self) -> None:
        """Lazy-load the ColPali model on first use."""
        if self._model is not None:
            return

        try:
            import torch
            from colpali_engine.models import ColPali
            from colpali_engine.models.paligemma.colpali_processing import ColPaliProcessor

            console.print(
                f"[dim]Loading ColPali model {self.model_id} on {self.device}...[/dim]"
            )

            # Enforce dynamic precision based on hardware
            dtype = torch.bfloat16 if self.device != "cpu" else torch.float32

            self._model = (
                ColPali.from_pretrained(
                    self.model_id,
                    torch_dtype=dtype,
                    device_map=self.device
                )
                .eval()
            )
            self._processor = ColPaliProcessor.from_pretrained(self.model_id)

        except ImportError as exc:
            raise ImportError(
                "VisionRAG requires additional machine learning packages.\n"
                "Install them with: pip install -e '.[vision]'"
            ) from exc
        except Exception as exc:
            console.print(f"[bold red]Failed to load vision model:[/bold red] {exc}")
            raise

    def index_pdf(self, path: Path) -> List[dict[str, Any]]:
        """
        Rasterize each PDF page to a high-DPI image and return patch-based embeddings.
        """
        try:
            import torch
            import pdf2image
            from PIL import Image
        except ImportError as exc:
            raise ImportError(
                "pdf2image and Pillow are required for PDF rasterization.\n"
                "Install them with: pip install -e '.[vision]'"
            ) from exc

        self.load_model()
        console.print(f"[cyan]VisionRAG:[/cyan] Converting {path.name} to images at 150 DPI...")
        
        # Convert pages to Pillow images
        images = pdf2image.convert_from_path(str(path), dpi=150)
        results: List[dict[str, Any]] = []
        
        batch_size = 4
        for i in range(0, len(images), batch_size):
            batch_images = images[i : i + batch_size]

            # Cache the rasterized pages
            for j, img in enumerate(batch_images):
                page_num = i + j + 1
                img_path = self.cache_dir / f"{path.stem}_page_{page_num}.jpg"
                img.save(img_path, "JPEG")

            # Multi-vector embedding extraction using ColPali strategy
            with torch.no_grad():
                batch = self._processor.process_images(batch_images).to(self.device)
                outputs = self._model(**batch)
                
                # Single-vector pooling: mean pool the contextualized patch tokens 
                # to fit standard ChromaDB dimension schemas
                pooled_embeddings = outputs.mean(dim=1).cpu().float().numpy()

            for j, emb in enumerate(pooled_embeddings):
                page_num = i + j + 1
                img_path = self.cache_dir / f"{path.stem}_page_{page_num}.jpg"

                results.append(
                    {
                        "source": str(path),
                        "page_num": page_num,
                        "embedding": emb.tolist(),
                        "image_path": str(img_path),
                        "text": f"[VISION EMBEDDING] Page {page_num} of {path.name}",
                        "type": "vision_page",
                    }
                )

        return results

    def embed_query(self, query: str) -> List[float]:
        """Generate a pooled visual search query vector."""
        try:
            import torch
        except ImportError as exc:
            raise ImportError("PyTorch is required for query embedding.") from exc

        self.load_model()

        with torch.no_grad():
            batch = self._processor.process_queries([query]).to(self.device)
            outputs = self._model(**batch)
            pooled = outputs.mean(dim=1).cpu().float().numpy()

        return [float(x) for x in pooled[0].tolist()]

    def is_available(self) -> bool:
        """Verify if all required libraries for VisionRAG are installed."""
        try:
            import colpali_engine
            import pdf2image
            import PIL.Image
            import torch
            return True
        except ImportError:
            return False
