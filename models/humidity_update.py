from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class HumidityUpdate:
    source: str
    type: str
    humidity: float
    time_of_event: str