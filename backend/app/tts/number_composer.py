"""NumberComposer: decomposes numeric financial amounts into grammatical national language words
and sequential audio clip tokens for Ewondo, Duala, and Fulfulde.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VerbalizedNumber:
    amount: int
    text: str
    tokens: list[str] = field(default_factory=list)


class NumberComposer:
    """Decomposes integers from 0 to 999,999,999 FCFA using national language grammar."""

    @classmethod
    def compose(cls, amount: int, number_rules: dict, include_currency: bool = True) -> VerbalizedNumber:
        if amount < 0:
            sub = cls.compose(abs(amount), number_rules, include_currency=include_currency)
            return VerbalizedNumber(
                amount=amount,
                text=f"- {sub.text}",
                tokens=["math_minus"] + sub.tokens,
            )

        units = number_rules.get("units", {})
        tens = number_rules.get("tens", {})
        hundred_word = number_rules.get("hundred", "ntet")
        thousand_word = number_rules.get("thousand", "tósen")
        million_word = number_rules.get("million", "miliɔn")
        conn = number_rules.get("connector", "a")
        cur_word = number_rules.get("currency_word", "FCFA")

        words: list[str] = []
        tokens: list[str] = []

        if amount == 0:
            words.append(units.get("0", "0"))
            tokens.append("num_0")
        else:
            millions = amount // 1_000_000
            remainder = amount % 1_000_000
            thousands = remainder // 1_000
            units_part = remainder % 1_000

            if millions > 0:
                m_words, m_tokens = cls._compose_under_1000(millions, units, tens, hundred_word, conn)
                words.extend(m_words)
                tokens.extend(m_tokens)
                words.append(million_word)
                tokens.append("unit_million")
                if thousands > 0 or units_part > 0:
                    words.append(conn)

            if thousands > 0:
                t_words, t_tokens = cls._compose_under_1000(thousands, units, tens, hundred_word, conn)
                words.extend(t_words)
                tokens.extend(t_tokens)
                words.append(thousand_word)
                tokens.append("unit_thousand")
                if units_part > 0:
                    words.append(conn)

            if units_part > 0:
                u_words, u_tokens = cls._compose_under_1000(units_part, units, tens, hundred_word, conn)
                words.extend(u_words)
                tokens.extend(u_tokens)

        if include_currency and cur_word:
            words.append(cur_word)
            tokens.append("currency_cfa")

        return VerbalizedNumber(
            amount=amount,
            text=" ".join(words),
            tokens=tokens,
        )

    @classmethod
    def _compose_under_1000(
        cls,
        val: int,
        units: dict,
        tens: dict,
        hundred_word: str,
        conn: str,
    ) -> tuple[list[str], list[str]]:
        words: list[str] = []
        tokens: list[str] = []

        h = val // 100
        rem = val % 100

        if h > 0:
            if h == 1:
                words.append(hundred_word)
                tokens.append("num_100")
            else:
                words.append(hundred_word)
                tokens.append("unit_hundred")
                u_str = units.get(str(h), str(h))
                words.append(u_str)
                tokens.append(f"num_{h}")
            if rem > 0:
                words.append(conn)

        if rem > 0:
            t = (rem // 10) * 10
            u = rem % 10
            if t > 0:
                t_str = tens.get(str(t), str(t))
                words.append(t_str)
                tokens.append(f"num_{t}")
                if u > 0:
                    words.append(conn)
                    words.append(units.get(str(u), str(u)))
                    tokens.append(f"num_{u}")
            else:
                words.append(units.get(str(u), str(u)))
                tokens.append(f"num_{u}")

        return words, tokens
