from dataclasses import dataclass

from dataclasses_json import LetterCase, dataclass_json


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SensorUpdate:
    source: str
    probe_id: str
    type: str
    value: float
    time_of_event: str
    device: str
    manufacturer: str
    platform: str
    app_version: str
