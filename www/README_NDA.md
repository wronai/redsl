# NDA — Automatyczne generowanie umowy

System umożliwia klientom samodzielne wygenerowanie i podpisanie umowy NDA przed rozpoczęciem współpracy.

## Flow

```
1. Klient wchodzi na /nda-form
2. Wprowadza NIP → system pobiera dane firmy z REGON/GUS
3. Uzupełnia dane osoby kontaktowej
4. System generuje gotową umowę NDA
5. Klient pobiera PDF, podpisuje, uploaduje lub wysyła email
6. My weryfikujemy i aktywujemy konto
```

## Pliki

| Plik | Opis |
|------|------|
| `nda-form.php` | Formularz 3-krokowy: NIP → Dane → Generowanie |
| `nda-wzor.php` | Redirect do formularza |

## Kroki

### Krok 1: NIP
- Wprowadzenie numeru NIP (10 cyfr)
- Automatyczne pobranie danych z REGON (w produkcji: GUS API)
- Fallback: ręczne wprowadzenie danych

### Krok 2: Dane firmy
Weryfikacja i uzupełnienie:
- Nazwa firmy
- Adres (ulica, kod, miasto)
- REGON, KRS
- Osoba reprezentująca (imię, nazwisko, stanowisko)
- Kontakt (email, telefon)

### Krok 3: Generowanie NDA
- Podgląd umowy w przeglądarce
- Pobieranie TXT (w produkcji: PDF z podpisem elektronicznym)
- Opcje przesłania:
  - Upload podpisanego skanu (PDF/JPG/PNG)
  - Wysłanie na nda@redsl.io
  - E-podpis (w przyszłości)

## Automatyzacja via NIP

W produkcji integracja z:
- **GUS REGON API** — pobieranie danych firmy po NIP
- **CEIDG** — dodatkowe weryfikacje dla działalności gospodarczych
- **KRS** — weryfikacja spółek

## Szablon NDA

Umowa zawiera standardowe klauzule:
- Definicję Informacji Poufnych (kod, dokumentacja, dostępy)
- Zobowiązania Odbiorcy (zachowanie poufności, brak ujawniania)
- Wyłączenia (publiczne, niezależnie opracowane)
- Okres ochrony: 3 lata
- Zwrot/utylizację informacji
- Prawo własności intelektualnej
- Odpowiedzialność odszkodowawczą

## CTA w interfejsie

### W sekcji Bezpieczeństwa (index.php)
```
[NDA] — podpisywane przed pierwszym skanem (link do /nda-form)
```

### W stopce (index.php)
```
Prawne > Wzór NDA → /nda-form
```

### W emailu powitalnym
```
Przed rozpoczęciem skanu, podpisz NDA:
https://redsl.io/nda-form?token=xxx
```

## Demo

```bash
# Formularz NDA
curl http://localhost:8080/nda-form

# Z NIP 1234567890 (demo data)
# NIP 0000000000 (manual entry)
```

## Wymagania produkcyjne

- GUS REGON API access (SOAP)
- Generowanie PDF (wkhtmltopdf lub lib PDF)
- Upload plików (AWS S3 lub local storage)
- Email notifications
- E-podisg integracja (np. DocuSign, Adobe Sign, polskie providerzy)

## Przykład integracji GUS (pseudocode)

```php
$client = new SoapClient('https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc');
$sid = $client->Zaloguj(['pKluczUzytkownika' => API_KEY]);
$company = $client->DaneSzukaj([
    'pParametryWyszukiwania' => ['Nip' => $nip]
], null, ['sid' => $sid]);
```
