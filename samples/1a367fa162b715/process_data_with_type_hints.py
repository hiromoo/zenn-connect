from typing import Union, List, Dict


def process_data(
    data: Union[List[int], Dict[str, int]],
) -> Union[List[int], Dict[str, int]]:
    if isinstance(data, list):
        return [x * 2 for x in data]
    elif isinstance(data, dict):
        return {k: v * 2 for k, v in data.items()}
