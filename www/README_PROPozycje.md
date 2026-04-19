# System wyboru propozycji (SaaS Panel)

Interfejs do wyboru ticketów refaktoryzacji przez klientów.

## Flow

```
1. Analiza kodu → Generowanie propozycji
2. Email powiadomienie z linkiem do /propozycje.php?token=xxx
3. Klient wybiera: "1, 3, 7, 12-15" / "wszystkie" / "wszystko pod 15"
4. Potwierdzenie → Backend tworzy zlecenia
5. Płatność po zmergeowaniu PR
```

## Pliki

| Plik | Opis |
|------|------|
| `propozycje.php` | Panel wyboru (UI) |
| `email-notifications.php` | Backend email + generowanie tokenów |

## Format wyboru

Klient może wpisać:

- `1, 3, 7` — pojedyncze tickety
- `12-15` — zakres (12, 13, 14, 15)
- `1, 3, 7, 12-15, 24` — kombinacja
- `wszystkie` — cała lista
- `wszystko pod 15` — wszystkie tickety poniżej 15 zł

## Cennik

- **10 zł** za ticket (do 500 LOC)
- Płatność **po zmergeowaniu PR**
- Brak subskrypcji
- NDA przed skanem

## Email Template

```
Subject: ReDSL — Analiza kodu gotowa: {project}

Zidentyfikowaliśmy {count} obszarów do refaktoryzacji.

[1] Refaktoryzacja klasy UserService (M, ~150 LOC)
[2] Ekstrakcja metod w PaymentController (S, ~80 LOC)
...

CENA: 10 zł za ticket
RAZEM: {total} zł za wszystkie

WYBIERZ KTÓRE CHCESZ:
https://redsl.io/propozycje.php?token=xxx
```

## Demo

```bash
# Test wysyłki email
curl -X POST "http://localhost:8080/email-notifications.php?demo=send" \
  -d "email=test@example.com" \
  -d "project=MyApp"
```

## Token dostępu

- Generowany: `generateAccessToken(projectId, email)`
- Walidacja: `verifyAccessToken(token)`
- Wygaśnięcie: 24h
- W produkcji: użyć JWT

## Wymagania

- PHP 8.2+
- Moduł `mail()` lub integracja z SendGrid/Mailgun
- `TOKEN_SECRET` w `.env`

## Przykłady użycia

### Wybór w panelu
```
[✓] Wszystkie propozycje                    80 zł
[ ] Wszystko poniżej 15 zł                  80 zł
[✓] Własny wybór: [1, 3, 7, 12-15, 24]     50 zł
```

### Wybór przez email reply
```
Klient odpowiada na email:
"Potwierdzam 1, 3, 7"

System parsuje i generuje zamówienie.
```
