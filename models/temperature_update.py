from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TemperatureUpdate:
    source: str
    type: str
    temperature: float
    time_of_event: str