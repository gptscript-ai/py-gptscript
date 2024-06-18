from typing import Any


class Text:
    def __init__(self,
                 fmt: str = "",
                 text: str = "",
                 ):
        if fmt == "" and text.startswith("!"):
            fmt = text[1:text.index("\n")]
            text = text.removeprefix("!" + fmt).strip()

        self.format = fmt
        self.text = text

    def to_json(self) -> dict[str, Any]:
        text = self.text + "\n"
        if self.format != "":
            text = "!" + self.format + "\n" + text

        return {"textNode": {"text": text}}
