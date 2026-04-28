from typing import Annotated, Any, TypeAlias

MessageDataType = dict[str, Any]
RedisKeyTTL: TypeAlias = Annotated[int, 'sec']
