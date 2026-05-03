"""
Gera senhas fortes e seus hashes bcrypt para o secrets.toml.

Padrão de melhores práticas:
- 16 caracteres
- Mistura de maiúsculas, minúsculas, dígitos e símbolos
- Geração via secrets module (CSPRNG)
- Exclui caracteres ambíguos visualmente (O/0, l/1/I)
- bcrypt cost factor 12 (~250ms por hash, atual recomendação OWASP)

Uso:
    python scripts/gen_credentials.py
"""
from __future__ import annotations

import secrets
import string

import bcrypt


# Conjuntos sem caracteres ambíguos (O, 0, l, 1, I)
LOWER = "abcdefghijkmnopqrstuvwxyz"   # sem 'l'
UPPER = "ABCDEFGHJKLMNPQRSTUVWXYZ"    # sem 'I' e 'O'
DIGITS = "23456789"                   # sem '0' e '1'
SYMBOLS = "!@#$%&*+-_?"

ALL_CHARS = LOWER + UPPER + DIGITS + SYMBOLS
TARGET_LENGTH = 16


def gen_password() -> str:
    """Gera senha garantindo pelo menos 1 char de cada categoria."""
    # Pelo menos 1 de cada categoria, completa o resto random
    pwd_chars = [
        secrets.choice(LOWER),
        secrets.choice(UPPER),
        secrets.choice(DIGITS),
        secrets.choice(SYMBOLS),
    ]
    pwd_chars += [secrets.choice(ALL_CHARS) for _ in range(TARGET_LENGTH - 4)]
    # Embaralha para não ter padrão previsível
    secrets.SystemRandom().shuffle(pwd_chars)
    return "".join(pwd_chars)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def main():
    usuarios = [
        ("ariane", "Ariane", "estudante", "arianemoreira4@hotmail.com"),
        ("romel", "Romel", "admin", "romel.dvasconcelos@gmail.com"),
    ]

    print("=" * 70)
    print("CREDENCIAIS GERADAS — Sefaz CE 2026")
    print("=" * 70)
    print()

    for username, nome, perfil, email in usuarios:
        senha = gen_password()
        h = hash_password(senha)
        print(f"### Usuário: {username} ({nome}) — {perfil}")
        print(f"Email: {email}")
        print(f"Senha: {senha}")
        print()
        print(f"[users.{username}]")
        print(f'nome = "{nome}"')
        print(f'senha_hash = "{h}"')
        print(f'perfil = "{perfil}"')
        print()
        print("-" * 70)
        print()


if __name__ == "__main__":
    main()
