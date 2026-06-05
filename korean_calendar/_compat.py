"""작은 외부 의존 호환 도구."""


class bidict(dict):
    """프로젝트에서 쓰는 범위만 지원하는 간단한 양방향 딕셔너리."""

    @property
    def inverse(self):
        return {value: key for key, value in self.items()}
