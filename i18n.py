"""Very small i18n layer: Polish (default) and English.

Usage in Python:   t("key", name="x")
Usage in Jinja:    {{ t("key", name="x") }}   /   {{ tp("plural.key", n) }}
The language is stored in the "lang" cookie and switched via /lang/<code>.
"""
from flask import has_request_context, request

DEFAULT_LANG = "pl"
LANGUAGES = {"pl": "Polski", "en": "English"}

TRANSLATIONS = {
    # ------------------------------------------------------------------ common
    "app.tagline": {"pl": "Trener testów teoretycznych", "en": "Theory test trainer"},
    "nav.base": {"pl": "Baza", "en": "Base"},
    "nav.signed_in_as": {"pl": "Zalogowano jako", "en": "Signed in as"},
    "nav.sign_out": {"pl": "Wyloguj", "en": "Sign out"},
    "nav.language": {"pl": "Język", "en": "Language"},
    "footer.motto": {"pl": "Bezpieczeństwo przede wszystkim · Precyzja zawsze",
                     "en": "Safety first · Precision always"},
    "common.back_to_base": {"pl": "Powrót do bazy", "en": "Back to base"},
    "common.username": {"pl": "Nazwa użytkownika", "en": "Username"},
    "common.password": {"pl": "Hasło", "en": "Password"},
    "common.delete": {"pl": "Usuń", "en": "Delete"},

    # ------------------------------------------------------------------ modes
    "mode.easy": {"pl": "Łatwy", "en": "Easy"},
    "mode.medium": {"pl": "Średni", "en": "Medium"},
    "mode.hard": {"pl": "Trudny", "en": "Hard"},
    "mode.impossible": {"pl": "Niemożliwy", "en": "Impossible"},
    "mode.easy.desc": {"pl": "Bez limitu błędów. Czysty trening — ucz się we własnym tempie.",
                       "en": "Unlimited mistakes. Pure training — learn at your own pace."},
    "mode.medium.desc": {"pl": "Możesz popełnić do 5 błędów. Szósty kończy test.",
                         "en": "You may make up to 5 mistakes. The 6th one ends the test."},
    "mode.hard.desc": {"pl": "Tylko 2 błędy. Zachowaj czujność.",
                       "en": "Only 2 mistakes allowed. Stay sharp."},
    "mode.impossible.desc": {"pl": "Zero tolerancji. Jeden błąd i misja zakończona.",
                             "en": "Zero tolerance. One mistake and the mission is over."},
    "mode.unlimited": {"pl": "bez limitu błędów", "en": "unlimited mistakes"},
    "mode.allowed": {"pl": "dozwolone błędy: {n}", "en": "{n} mistakes allowed"},
    "mode.allowed_one": {"pl": "dozwolone błędy: {n}", "en": "{n} mistake allowed"},

    # ------------------------------------------------------------------ status
    "status.passed": {"pl": "Zaliczony", "en": "Passed"},
    "status.failed": {"pl": "Niezaliczony", "en": "Failed"},
    "status.abandoned": {"pl": "Przerwany", "en": "Abandoned"},
    "status.active": {"pl": "W toku", "en": "In progress"},

    # ------------------------------------------------------------------ auth
    "login.title": {"pl": "Logowanie", "en": "Sign in"},
    "login.kicker": {"pl": "Kontrola dostępu", "en": "Access control"},
    "login.lead": {"pl": "Zamelduj się, aby kontynuować szkolenie.",
                   "en": "Report for duty to continue your training."},
    "login.remember": {"pl": "Nie wylogowuj mnie", "en": "Keep me signed in"},
    "login.submit": {"pl": "Zaloguj się", "en": "Sign in"},
    "login.no_account": {"pl": "Nie masz konta?", "en": "No account yet?"},
    "login.enlist": {"pl": "Zarejestruj się", "en": "Enlist now"},
    "register.title": {"pl": "Załóż konto", "en": "Create account"},
    "register.kicker": {"pl": "Nowy rekrut", "en": "New recruit"},
    "register.lead": {"pl": "Wybierz kryptonim i hasło.", "en": "Pick a call sign and a password."},
    "register.username_hint": {"pl": "Litery, cyfry, kropka, myślnik lub podkreślnik",
                               "en": "Letters, digits, dot, dash or underscore"},
    "register.confirm": {"pl": "Powtórz hasło", "en": "Repeat password"},
    "register.code": {"pl": "Kod dostępu strzelnicy", "en": "Range access code"},
    "register.code_hint": {"pl": "Otrzymasz go od obsługi strzelnicy.",
                           "en": "You can get it from the range staff."},
    "register.submit": {"pl": "Załóż konto", "en": "Create account"},
    "register.have_account": {"pl": "Masz już konto?", "en": "Already enlisted?"},
    "register.sign_in": {"pl": "Zaloguj się", "en": "Sign in"},

    "flash.login_required": {"pl": "Zaloguj się, aby kontynuować.", "en": "Please sign in to continue."},
    "flash.bad_code": {"pl": "Nieprawidłowy kod dostępu. Poproś obsługę strzelnicy o aktualny kod.",
                       "en": "Invalid access code. Ask the range staff for the current code."},
    "flash.bad_username": {"pl": "Nazwa użytkownika: 3–40 znaków — litery, cyfry, kropka, myślnik lub podkreślnik.",
                           "en": "Username must be 3–40 characters: letters, digits, dot, dash or underscore."},
    "flash.short_password": {"pl": "Hasło musi mieć co najmniej 6 znaków.",
                             "en": "Password must be at least 6 characters long."},
    "flash.password_mismatch": {"pl": "Hasła nie są identyczne.", "en": "Passwords don't match."},
    "flash.username_taken": {"pl": "Ta nazwa użytkownika jest już zajęta.", "en": "This username is already taken."},
    "flash.welcome": {"pl": "Witaj w oddziale, {name}!", "en": "Welcome aboard, {name}!"},
    "flash.bad_login": {"pl": "Nieprawidłowa nazwa użytkownika lub hasło.", "en": "Wrong username or password."},
    "flash.signed_out": {"pl": "Wylogowano.", "en": "You have been signed out."},

    # ------------------------------------------------------------------ dashboard
    "dash.title": {"pl": "Baza", "en": "Base"},
    "dash.kicker": {"pl": "Baza", "en": "Home base"},
    "dash.greeting": {"pl": "Witaj, {name}!", "en": "Ready, {name}?"},
    "dash.step": {"pl": "Krok {n}", "en": "Step {n}"},
    "dash.load_bank": {"pl": "Wczytaj bazę pytań", "en": "Load question bank"},
    "dash.drop": {"pl": "Upuść tutaj plik .xlsx", "en": "Drop your .xlsx here"},
    "dash.drop_or": {"pl": "lub kliknij, aby wybrać plik", "en": "or tap to choose a file"},
    "dash.title_field": {"pl": "Tytuł", "en": "Title"},
    "dash.optional": {"pl": "(opcjonalnie)", "en": "(optional)"},
    "dash.title_placeholder": {"pl": "np. Bezpieczeństwo na strzelnicy — poziom 1",
                               "en": "e.g. Range safety — level 1"},
    "dash.load_submit": {"pl": "Wczytaj i kontynuuj", "en": "Load and continue"},
    "dash.format": {"pl": "Format pliku", "en": "File format"},
    "dash.col_id": {"pl": "ID pytania", "en": "Question ID"},
    "dash.col_question": {"pl": "Pytanie", "en": "Question"},
    "dash.col_options": {"pl": "Warianty odpowiedzi", "en": "Answer options"},
    "dash.col_correct": {"pl": "Poprawna odpowiedź: A/B/C, C/D/E, 1/2/3 lub dokładny tekst odpowiedzi",
                         "en": "Correct answer: A/B/C, C/D/E, 1/2/3 or the exact option text"},
    "dash.format_note": {"pl": "Wiersz nagłówka jest wykrywany automatycznie. Odczytywany jest tylko pierwszy arkusz.",
                         "en": "A header row is detected automatically. Only the first sheet is read."},
    "dash.template": {"pl": "Pobierz szablon", "en": "Download template"},
    "dash.banks": {"pl": "Twoje bazy pytań", "en": "Your question banks"},
    "dash.start": {"pl": "Start", "en": "Start"},
    "dash.delete_confirm": {"pl": "Usunąć „{title}” wraz z historią?", "en": "Delete “{title}” and its history?"},
    "dash.empty": {"pl": "Brak baz pytań.", "en": "No question banks yet."},
    "dash.empty_hint": {"pl": "Wczytaj plik Excel, aby zacząć.", "en": "Upload an Excel file to get started."},
    "dash.record": {"pl": "Historia służby", "en": "Service record"},
    "dash.recent": {"pl": "Ostatnie testy", "en": "Recent tests"},
    "dash.th_date": {"pl": "Data", "en": "Date"},
    "dash.th_bank": {"pl": "Baza pytań", "en": "Bank"},
    "dash.th_mode": {"pl": "Tryb", "en": "Mode"},
    "dash.th_score": {"pl": "Wynik", "en": "Score"},
    "dash.th_result": {"pl": "Rezultat", "en": "Result"},
    "dash.resume": {"pl": "Wznów", "en": "Resume"},
    "dash.report": {"pl": "Raport", "en": "Report"},

    "flash.duplicate": {"pl": "Ta baza pytań jest już wczytana jako „{title}”. Otwieram ją.",
                        "en": "This question bank is already loaded as “{title}”. Opening it."},
    "flash.limit_reached": {"pl": "Możesz mieć maksymalnie {max} baz pytań. Usuń jedną, aby wczytać nową.",
                            "en": "You can keep up to {max} question banks. Delete one to upload a new one."},
    "flash.data_expired": {"pl": "Po {days} dniach bez aktywności Twoje bazy pytań i historia testów zostały usunięte. Konto pozostało.",
                           "en": "After {days} days without activity your question banks and test history were deleted. Your account is still here."},
    "dash.official": {"pl": "Oficjalna baza", "en": "Official bank"},
    "dash.official_note": {"pl": "dostępna zawsze", "en": "always available"},
    "dash.banks_count": {"pl": "{n} z {max}", "en": "{n} of {max}"},
    "dash.limit_full": {"pl": "Limit baz pytań osiągnięty ({max}). Usuń jedną z listy, aby wczytać nową.",
                        "en": "Question bank limit reached ({max}). Delete one from the list to upload a new one."},
    "dash.retention": {"pl": "Bazy pytań i historia testów są automatycznie usuwane po {days} dniach bez aktywności. Konto pozostaje.",
                       "en": "Question banks and test history are deleted automatically after {days} days without activity. Your account stays."},
    "flash.choose_file": {"pl": "Najpierw wybierz plik Excel.", "en": "Choose an Excel file first."},
    "flash.only_xlsx": {"pl": "Obsługiwane są tylko pliki .xlsx. W Excelu użyj „Zapisz jako → Skoroszyt programu Excel (.xlsx)”.",
                        "en": "Only .xlsx files are supported. In Excel use “Save as → Excel Workbook (.xlsx)”."},
    "flash.loaded": {"pl": "Baza pytań wczytana.", "en": "Question bank loaded."},
    "flash.deleted": {"pl": "Usunięto „{title}”.", "en": "“{title}” was deleted."},
    "flash.too_large": {"pl": "Plik jest za duży. Limit to 5 MB.", "en": "The file is too large. The limit is 5 MB."},
    "flash.select_mode": {"pl": "Wybierz poziom trudności.", "en": "Select a difficulty level."},
    "flash.nothing_to_retry": {"pl": "Nie ma czego powtarzać — wszystkie odpowiedzi były poprawne.",
                               "en": "Nothing to retry — every question was answered correctly."},

    # ------------------------------------------------------------------ parser errors
    "parse.open_failed": {"pl": "Nie można otworzyć pliku. Wczytaj plik .xlsx.",
                          "en": "This file could not be opened. Please upload an .xlsx file."},
    "parse.too_many": {"pl": "Za dużo wierszy. Limit to {n} pytań w pliku.",
                       "en": "Too many rows. The limit is {n} questions per file."},
    "parse.empty_sheet": {"pl": "Pierwszy arkusz jest pusty.", "en": "The first worksheet is empty."},
    "parse.problems": {"pl": "Liczba problemów w pliku: {n}. Popraw je i wczytaj plik ponownie.",
                       "en": "Found {n} problem(s) in the file. Fix them and upload again."},
    "parse.no_questions": {"pl": "W pliku nie znaleziono pytań.", "en": "No questions were found in the file."},
    "parse.row_bad_answer": {"pl": "Wiersz {row}: poprawna odpowiedź „{answer}” nie pasuje do żadnego wariantu.",
                             "en": "Row {row}: correct answer “{answer}” doesn't match any option."},
    "parse.row_no_text": {"pl": "Wiersz {row}: brak treści pytania (kolumna B).",
                          "en": "Row {row}: question text (column B) is empty."},
    "parse.row_few_options": {"pl": "Wiersz {row}: wymagane są co najmniej dwa warianty odpowiedzi (C–E).",
                              "en": "Row {row}: at least two answer options (C–E) are required."},
    "parse.row_empty_correct": {"pl": "Wiersz {row}: poprawna odpowiedź wskazuje na pusty wariant.",
                                "en": "Row {row}: the correct answer points to an empty option."},
    "parse.empty_value": {"pl": "(puste)", "en": "(empty)"},

    # ------------------------------------------------------------------ briefing
    "brief.title": {"pl": "Odprawa", "en": "Briefing"},
    "brief.kicker": {"pl": "Odprawa przed misją", "en": "Mission briefing"},
    "brief.lead": {"pl": "Wczytane pytania: {n}. Wybierz poziom trudności.",
                   "en": "{n} questions loaded. Select your difficulty."},
    "brief.difficulty": {"pl": "Poziom trudności", "en": "Difficulty"},
    "brief.shuffle_q": {"pl": "Losowa kolejność pytań", "en": "Shuffle questions"},
    "brief.shuffle_a": {"pl": "Losowa kolejność odpowiedzi", "en": "Shuffle answers"},
    "brief.questions": {"pl": "Liczba pytań", "en": "Questions"},
    "brief.of": {"pl": "z {n}", "en": "of {n}"},
    "brief.begin": {"pl": "Rozpocznij test", "en": "Begin test"},

    # ------------------------------------------------------------------ test
    "test.title": {"pl": "Test w toku", "en": "Test in progress"},
    "test.question": {"pl": "Pytanie", "en": "Question"},
    "test.hits": {"pl": "Trafienia", "en": "Hits"},
    "test.misses": {"pl": "Pudła", "en": "Misses"},
    "test.answers": {"pl": "Odpowiedzi", "en": "Answers"},
    "test.loading": {"pl": "Ładowanie…", "en": "Loading…"},
    "test.next": {"pl": "Dalej", "en": "Next"},
    "test.finish": {"pl": "Zakończ", "en": "Finish"},
    "test.tip": {"pl": "Wskazówka: naciśnij {keys}, aby odpowiedzieć", "en": "Tip: press {keys} to answer"},
    "test.abort": {"pl": "Przerwij test", "en": "Abort test"},
    "test.abort_confirm": {"pl": "Przerwać test? Zostanie zapisany jako przerwany.",
                           "en": "Abort this test? It will be recorded as abandoned."},
    "test.view_debrief": {"pl": "Zobacz raport", "en": "View debrief"},

    # strings used by static/js/test.js
    "js.unlimited": {"pl": "∞ bez limitu", "en": "∞ unlimited"},
    "js.kia": {"pl": "Brak HP", "en": "K.I.A."},
    "js.last_life": {"pl": "ostatnie życie", "en": "last life"},
    "js.left": {"pl": "zapas błędów: {n}", "en": "{n} mistakes left"},
    "js.left_one": {"pl": "zapas błędów: {n}", "en": "{n} mistake left"},
    "js.misses_count": {"pl": "pudła: {n}", "en": "{n} misses"},
    "js.misses_count_one": {"pl": "pudła: {n}", "en": "{n} miss"},
    "js.hit": {"pl": "Trafienie", "en": "Hit"},
    "js.miss": {"pl": "Pudło", "en": "Miss"},
    "js.correct": {"pl": "Poprawna odpowiedź.", "en": "Correct answer."},
    "js.wrong": {"pl": "Poprawna odpowiedź jest zaznaczona na zielono.",
                 "en": "The correct answer is highlighted in green."},
    "js.all_cleared": {"pl": "Wszystkie pytania zaliczone", "en": "All questions cleared"},
    "js.out_of_hp": {"pl": "Brak HP", "en": "Out of HP"},
    "js.complete": {"pl": "Test zakończony", "en": "Test complete"},
    "js.accomplished": {"pl": "Misja wykonana", "en": "Mission accomplished"},
    "js.failed": {"pl": "Misja nieudana", "en": "Mission failed"},
    "js.reconnecting": {"pl": "Łączenie z serwerem…", "en": "Connecting to the server…"},
    "js.retry": {"pl": "Spróbuj ponownie", "en": "Try again"},
    "js.connection": {"pl": "Problem z połączeniem. Spróbuj ponownie.", "en": "Connection problem. Try again."},
    "js.load_failed": {"pl": "Nie udało się wczytać testu.",
                       "en": "Could not load the test."},

    # ------------------------------------------------------------------ results
    "res.title": {"pl": "Raport", "en": "Debrief"},
    "res.kicker": {"pl": "Raport", "en": "Debrief"},
    "res.accomplished": {"pl": "Misja wykonana", "en": "Mission accomplished"},
    "res.aborted": {"pl": "Misja przerwana", "en": "Mission aborted"},
    "res.failed": {"pl": "Misja nieudana", "en": "Mission failed"},
    "res.out_of_hp": {"pl": "Zabrakło HP — liczba błędów: {n}.", "en": "You ran out of HP after {n} mistakes."},
    "res.out_of_hp_one": {"pl": "Zabrakło HP — liczba błędów: {n}.", "en": "You ran out of HP after {n} mistake."},
    "res.below_mark": {"pl": "Wynik poniżej progu zaliczenia ({p}%).", "en": "Score below the {p}% pass mark."},
    "res.above_mark": {"pl": "Próg zaliczenia ({p}%) osiągnięty.", "en": "Score at or above the {p}% pass mark."},
    "res.within_limit": {"pl": "Wszystkie pytania ukończone w limicie błędów.",
                         "en": "All questions answered within the allowed mistakes."},
    "res.stamp_pass": {"pl": "Zaliczony", "en": "Passed"},
    "res.stamp_fail": {"pl": "Niezaliczony", "en": "Failed"},
    "res.stamp_abort": {"pl": "Przerwany", "en": "Aborted"},
    "res.hits": {"pl": "Trafienia", "en": "Hits"},
    "res.misses": {"pl": "Pudła", "en": "Misses"},
    "res.not_reached": {"pl": "Bez odpowiedzi", "en": "Not reached"},
    "res.mode": {"pl": "Tryb", "en": "Mode"},
    "res.time": {"pl": "Czas", "en": "Time"},
    "res.questions": {"pl": "Pytania", "en": "Questions"},
    "res.retry": {"pl": "Powtórz w tym trybie", "en": "Retry same mode"},
    "res.drill_missed": {"pl": "Ćwicz błędne ({n})", "en": "Drill missed ({n})"},
    "res.change_mode": {"pl": "Zmień tryb", "en": "Change mode"},
    "res.review": {"pl": "Przegląd pytań", "en": "Question review"},
    "res.all": {"pl": "Wszystkie", "en": "All"},
    "res.tag_hit": {"pl": "Trafienie", "en": "Hit"},
    "res.tag_miss": {"pl": "Pudło", "en": "Miss"},
    "res.tag_unanswered": {"pl": "Bez odpowiedzi", "en": "Not reached"},
    "res.your_answer": {"pl": "twoja odpowiedź", "en": "your answer"},
    "res.correct": {"pl": "poprawna", "en": "correct"},

    # ------------------------------------------------------------------ errors
    "error.title": {"pl": "Błąd {code}", "en": "Error {code}"},
    "error.server": {"pl": "Błąd serwera. Spróbuj ponownie za chwilę.", "en": "Server error. Please try again in a moment."},
    "error.not_found": {"pl": "Cel nie został znaleziony.", "en": "Target not found."},

    # ------------------------------------------------------------------ Excel template
    "tpl.sheet": {"pl": "Pytania", "en": "Questions"},
    "tpl.filename": {"pl": "szablon_pytan.xlsx", "en": "question_template.xlsx"},
}

# Keys exposed to the test page JavaScript
JS_KEYS = [k for k in TRANSLATIONS if k.startswith("js.")]


def get_lang():
    if has_request_context():
        lang = request.cookies.get("lang")
        if lang in LANGUAGES:
            return lang
    return DEFAULT_LANG


def t(key, lang=None, **params):
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(lang or get_lang()) or entry[DEFAULT_LANG]
    return text.format(**params) if params else text


def tp(key, n, lang=None, **params):
    """Plural-aware lookup: uses '<key>_one' for n == 1 when it exists."""
    if n == 1 and f"{key}_one" in TRANSLATIONS:
        key = f"{key}_one"
    return t(key, lang=lang, n=n, **params)


def plural_pl(n, one, few, many):
    """Polish noun forms: 1 pytanie, 2–4 pytania, 5+ pytań (12–14 → many)."""
    if n == 1:
        return one
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return few
    return many


def count_questions(n, lang=None):
    lang = lang or get_lang()
    if lang == "pl":
        return f"{n} " + plural_pl(n, "pytanie", "pytania", "pytań")
    return f"{n} question" + ("" if n == 1 else "s")


def js_strings(lang=None):
    lang = lang or get_lang()
    return {k[3:]: t(k, lang=lang) for k in JS_KEYS}
