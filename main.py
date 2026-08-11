"""
תשבץ עברי - גרסה חדשה
משתמש ב-Firebase לטעינת הגדרות ופתרונות, ובונה תשבץ עצמאי ללא תלות באתר חיצוני.
כולל אחסון תמונות ב-FIREBASE
משתמש ההגדרות ב-realtime db
"""

import streamlit as st
import pandas as pd
import numpy as np
import streamlit.components.v1 as components
import firebase_admin
from firebase_admin import credentials, db, storage
import json
import random
import re
import os
import webbrowser
import datetime

# ---------------------------------------------------------------------------
# כיוון עברית ו-RTL
# ---------------------------------------------------------------------------
def to_hebrew():
    st.markdown(
        """
        <style>
        body { direction: rtl; text-align: right; font-size: 20px; }
        .stMarkdown p { direction: rtl; text-align: right; font-size: 20px; }

        /* אפס כיוון על ה-wrapper הראשי כדי ש-sidebar יישאר שמאלה */
        [data-testid="stAppViewContainer"] {
            direction: ltr !important;
        }
        /* החזר RTL לתוכן הראשי בלבד */
        [data-testid="stMainBlockContainer"] {
            direction: rtl !important;
            text-align: right !important;
        }
        /* sidebar תמיד שמאלה, טקסט RTL */
        [data-testid="stSidebar"] {
            left: 0 !important;
            right: auto !important;
            direction: rtl;
        }
        /* סליידר עצמו — LTR כדי ש-0 יהיה בצד שמאל והמספרים יגדלו ימינה */
        [data-testid="stSidebar"] [data-testid="stSlider"] {
            direction: ltr !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_bg(url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url('{url}');
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Firebase
# ---------------------------------------------------------------------------
FIREBASE_DB_URL = "https://hegyonit-default-rtdb.europe-west1.firebasedatabase.app/"
FIREBASE_BUCKET = "hegyonit.firebasestorage.app"


@st.cache_resource()
def init_firebase():
    try:
        firebase_admin.delete_app(firebase_admin.get_app())
    except ValueError:
        pass

    # Always use Streamlit Secrets on Cloud
    if "firebase" in st.secrets:
        cred_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cred_dict)
    else:
        # Local development only
        cred = credentials.Certificate(".streamlit/fb_cred.json")

    firebase_admin.initialize_app(cred, {
        "databaseURL": FIREBASE_DB_URL,
        "storageBucket": FIREBASE_BUCKET,
    })

def get_subjects():
    # DB structure: /{subject}/... — subjects are top-level keys
    ref = db.reference("/")
    data = ref.get()
    if data:
        return list(data.keys())
    return []


def get_words_from_firebase(subject: str):
    """
    Returns list of (pitaron, hagdara) pairs for the chosen subject.
    DB structure: /{subject}/{contributor}/{pitaron} = hagdara
    """
    ref = db.reference(f"/{subject}")
    data = ref.get()
    pairs = []
    if data:
        for contributor, clues in data.items():
            if isinstance(clues, dict):
                for pitaron, hagdara in clues.items():
                    # מפתח=פתרון, ערך=הגדרה → (פתרון_גולמי, הגדרה_לתצוגה)
                    pairs.append((pitaron.strip(), clean_hagdara(str(hagdara))))
    return pairs


# ---------------------------------------------------------------------------
# עיבוד מילים עבריות
# ---------------------------------------------------------------------------
FINAL_TO_NORMAL = str.maketrans("ןםףץך", "נמפצכ")


def normalize_answer(answer: str) -> str:
    """מסיר רווחים ומחליף אותיות סופיות."""
    answer = answer.replace(" ", "").replace("\u200f", "").replace("\u200e", "")
    answer = answer.translate(FINAL_TO_NORMAL)
    return answer.upper()


def clean_hagdara(hagdara: str) -> str:
    """מסיר קידומת מספר כמו '3. ' מתחילת ההגדרה."""
    return re.sub(r'^\d+[\.\)]\s*', '', hagdara).strip()


def build_clue_with_length(clue: str, answer_raw: str, answer_norm: str) -> str:
    """מוסיף בתחילת ההגדרה את אורך כל מילה בפתרון הגולמי."""
    words = [w for w in answer_raw.split() if w.strip()]
    if len(words) <= 1:
        length_str = f"({len(answer_norm)})"
    else:
        # היפוך סדר — עברית נקראת מימין לשמאל
        lengths = ",".join(str(len(w.strip())) for w in reversed(words))
        length_str = f"({lengths})"
    return f"{length_str} {clue}"


# ---------------------------------------------------------------------------
# אלגוריתם פריסת תשבץ
# ---------------------------------------------------------------------------
GRID_SIZE = 25
EMPTY = ""
BLACK = " "


def can_place(grid, dir_grid, word, row, col, horizontal):
    """
    בודק אם ניתן למקם 'word' ב-(row,col) בכיוון הנתון.
    חוקים:
    1. אין אות לפני/אחרי המילה (למנוע מיזוג מילים).
    2. כל תא ריק: אין שכנים ניצבים כלל.
    3. כל תא עם אות תואמת: חייב שהאות הגיעה מכיוון ההפוך (הצטלבות אמיתית).
    4. לא יותר מהצטלבות אחת עם אותה מילה קיימת.
    """
    n = len(word)
    # 'H' = horizontal placed, 'V' = vertical placed, '' = empty
    new_dir = 'H' if horizontal else 'V'
    cross_dir = 'V' if horizontal else 'H'

    if horizontal:
        if col + n > GRID_SIZE:
            return False
        if col > 0 and grid[row][col - 1] != EMPTY:
            return False
        if col + n < GRID_SIZE and grid[row][col + n] != EMPTY:
            return False
        for i, ch in enumerate(word):
            cell      = grid[row][col + i]
            cell_dir  = dir_grid[row][col + i]
            if cell == EMPTY:
                # תא ריק — אין שכנים מעל/מתחת
                above = grid[row - 1][col + i] if row > 0 else EMPTY
                below = grid[row + 1][col + i] if row < GRID_SIZE - 1 else EMPTY
                if above != EMPTY or below != EMPTY:
                    return False
            elif cell == ch:
                # תא תפוס — חייב להיות כיוון הפוך (הצטלבות אמיתית)
                if cell_dir != cross_dir:
                    return False
            else:
                return False   # קונפליקט אות
        return True
    else:  # vertical
        if row + n > GRID_SIZE:
            return False
        if row > 0 and grid[row - 1][col] != EMPTY:
            return False
        if row + n < GRID_SIZE and grid[row + n][col] != EMPTY:
            return False
        for i, ch in enumerate(word):
            cell      = grid[row + i][col]
            cell_dir  = dir_grid[row + i][col]
            if cell == EMPTY:
                left  = grid[row + i][col - 1] if col > 0 else EMPTY
                right = grid[row + i][col + 1] if col < GRID_SIZE - 1 else EMPTY
                if left != EMPTY or right != EMPTY:
                    return False
            elif cell == ch:
                if cell_dir != cross_dir:
                    return False
            else:
                return False
        return True


def place_word(grid, dir_grid, word, row, col, horizontal):
    new_dir = 'H' if horizontal else 'V'
    for i, ch in enumerate(word):
        if horizontal:
            grid[row][col + i]     = ch
            if dir_grid[row][col + i] == EMPTY:
                dir_grid[row][col + i] = new_dir
            # intersection cell keeps existing direction (cross_dir)
        else:
            grid[row + i][col]     = ch
            if dir_grid[row + i][col] == EMPTY:
                dir_grid[row + i][col] = new_dir


def count_intersections(grid, word, row, col, horizontal):
    count = 0
    for i, ch in enumerate(word):
        cell = grid[row][col + i] if horizontal else grid[row + i][col]
        if cell == ch:
            count += 1
    return count


def build_crossword(words_normalized):
    """
    בונה תשבץ ממילים מנורמלות.
    כאשר שתי מילים מתחילות באותו תא (אחת אופקית ואחת אנכית),
    הן חולקות את אותו מספר הגדרה.
    """
    grid       = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
    dir_grid   = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
    placements = []
    used_orig  = set()
    cell_to_num = {}   # (r,c) → מספר הגדרה כבר הוקצה לתא זה

    indexed      = list(enumerate(words_normalized))
    sorted_words = sorted(indexed, key=lambda x: -len(x[1]))

    placement_num = 1

    def assign_num(r, c):
        nonlocal placement_num
        if (r, c) in cell_to_num:
            return cell_to_num[(r, c)]
        cell_to_num[(r, c)] = placement_num
        placement_num += 1
        return cell_to_num[(r, c)]

    for orig_idx, word in sorted_words:
        if orig_idx in used_orig:
            continue
        if len(word) < 2:
            continue

        placed = False

        if placements:
            candidates = []
            for p_word, p_row, p_col, p_hor, _, _ in placements:
                for i, ch in enumerate(word):
                    for j, pch in enumerate(p_word):
                        if ch == pch:
                            if p_hor:
                                nr = p_row - i
                                nc = p_col + j
                                if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and nr + len(word) <= GRID_SIZE:
                                    if can_place(grid, dir_grid, word, nr, nc, False):
                                        score = count_intersections(grid, word, nr, nc, False)
                                        candidates.append((score, nr, nc, False))
                            else:
                                nr = p_row + j
                                nc = p_col - i
                                if 0 <= nc < GRID_SIZE and 0 <= nr < GRID_SIZE and nc + len(word) <= GRID_SIZE:
                                    if can_place(grid, dir_grid, word, nr, nc, True):
                                        score = count_intersections(grid, word, nr, nc, True)
                                        candidates.append((score, nr, nc, True))

            if candidates:
                candidates.sort(key=lambda x: -x[0])
                best_score = candidates[0][0]
                top    = [c for c in candidates if c[0] == best_score]
                chosen = random.choice(top[:5])
                _, nr, nc, hor = chosen
                place_word(grid, dir_grid, word, nr, nc, hor)
                num = assign_num(nr, nc)
                placements.append((word, nr, nc, hor, num, orig_idx))
                used_orig.add(orig_idx)
                placed = True

        if not placed:
            if not placements:
                r = GRID_SIZE // 2
                c = (GRID_SIZE - len(word)) // 2
                if can_place(grid, dir_grid, word, r, c, True):
                    place_word(grid, dir_grid, word, r, c, True)
                    num = assign_num(r, c)
                    placements.append((word, r, c, True, num, orig_idx))
                    used_orig.add(orig_idx)
            else:
                random_placed = False
                for _ in range(2000):
                    hor = random.choice([True, False])
                    if hor:
                        r = random.randint(0, GRID_SIZE - 1)
                        c = random.randint(0, GRID_SIZE - len(word))
                    else:
                        r = random.randint(0, GRID_SIZE - len(word))
                        c = random.randint(0, GRID_SIZE - 1)
                    if can_place(grid, dir_grid, word, r, c, hor):
                        place_word(grid, dir_grid, word, r, c, hor)
                        num = assign_num(r, c)
                        placements.append((word, r, c, hor, num, orig_idx))
                        used_orig.add(orig_idx)
                        random_placed = True
                        break


    return grid, placements


# ─── Firebase Storage — תמונות ───────────────────────────────────────────────
IMAGE_EXTENSIONS  = [".jpeg", ".jpg", ".png"]
SIGNED_URL_TTL    = datetime.timedelta(minutes=55)   # תוקף ה-Signed URL (קצר מה-cache)


def is_image_clue(clue_value: str) -> bool:
    return clue_value.strip().upper().startswith("IMG:")


def _storage_name(answer_raw: str) -> str:
    """
    ממיר שם פתרון לשם קובץ ב-Storage: רווחים → מקף.
    "מתי כספי" → "מתי-כספי"
    """
    return answer_raw.strip().replace(" ", "-")


def _name_variants(answer_raw: str) -> list[str]:
    """
    מייצר וריאנטים של שם הקובץ למקרה שהמפתח ב-DB שמר רווח / מקף / underscore.
    סדר הניסיון: מקף → רווח → underscore
    """
    base    = _storage_name(answer_raw)   # רווח → מקף (ברירת מחדל)
    raw     = answer_raw.strip()
    with_us = raw.replace(" ", "_")
    seen, variants = set(), []
    for v in [base, raw, with_us]:
        if v not in seen:
            seen.add(v)
            variants.append(v)
    return variants


@st.cache_data(ttl=3300, show_spinner=False)
def get_image_url(answer_raw: str, subject: str) -> str | None:
    """
    מחפש תמונה ב-Firebase Storage תחת images/{subject}/{answer-with-hyphens}.{ext}
    שם התיקייה נקבע לפי נושא התשבץ שנבחר.
    ומחזיר Signed URL בתוקף ~55 דקות (הקצר מה-cache TTL של 55 דקות).
    Storage rules: private → חייבים Signed URL; לא קוראים make_public.
    מחזיר None אם לא נמצאה תמונה.
    """
    storage_folder = f"images/{subject}"
    try:
        bucket = storage.bucket()
        for name in _name_variants(answer_raw):
            for ext in IMAGE_EXTENSIONS:
                blob = bucket.blob(f"{storage_folder}/{name}{ext}")
                if blob.exists():
                    url = blob.generate_signed_url(
                        expiration=SIGNED_URL_TTL,
                        method="GET",
                        version="v4",
                    )
                    return url
    except Exception as e:
        st.sidebar.warning(f"שגיאה בגישה ל-Storage: {e}", icon="⚠️")
    return None


@st.cache_data(ttl=3300, show_spinner=False)
def get_song_url(answer_raw: str) -> str | None:
    """
    מחפש שיר ב-Firebase Storage תחת songs/Hebrew/{answer-with-hyphens}.mp3
    ומחזיר Signed URL בתוקף ~55 דקות.
    מחזיר None אם לא נמצא שיר.
    """
    SONG_FOLDER = "songs/Hebrew"
    try:
        bucket = storage.bucket()
        for name in _name_variants(answer_raw):
            blob = bucket.blob(f"{SONG_FOLDER}/{name}.mp3")
            if blob.exists():
                url = blob.generate_signed_url(
                    expiration=SIGNED_URL_TTL,
                    method="GET",
                    version="v4",
                )
                return url
    except Exception as e:
        st.sidebar.warning(f"שגיאה בגישה לשירים ב-Storage: {e}", icon="⚠️")
    return None


def _open_image_anonymously(img_url: str) -> None:
    """
    פותח תמונה בדפדפן מבלי לחשוף את שם הקובץ בלשונית.
    מוריד את התמונה, מקודד ל-base64, כותב קובץ HTML זמני עם <title>תמונה</title>
    ופותח אותו — כך הלשונית מציגה "תמונה" ולא את שם הפתרון.
    """
    import base64
    import tempfile
    import urllib.request

    # הסק mime מסיומת הנתיב (לפני פרמטרי ה-query של ה-Signed URL)
    path_part = img_url.split("?")[0]
    ext  = os.path.splitext(path_part)[1].lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

    with urllib.request.urlopen(img_url) as resp:
        b64 = base64.b64encode(resp.read()).decode()

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>תמונה</title>
</head>
<body style="margin:0;background:#111;display:flex;
             align-items:center;justify-content:center;min-height:100vh;">
  <img src="data:{mime};base64,{b64}"
       style="max-width:100%;max-height:100vh;object-fit:contain;">
</body>
</html>"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write(html)
        tmp_path = f.name

    webbrowser.open(f"file:///{tmp_path}")


def display_clue_in_sidebar(clue_text: str, answer_raw: str = "", hagdara_raw: str = "", subject: str = ""):
    """
    מציג הגדרה בסייד-בר.
    - תמונה (אם קיימת) + כפתור "פתח תמונה"
    - נגן שיר עם st.audio (אם קיים שיר)
    - אחרת: הגדרה טקסטואלית
    """
    parts = clue_text.strip().split(" ", 1)
    if len(parts) == 2 and parts[0].startswith("(") and parts[0].endswith(")"):
        length_str = parts[0]
    else:
        length_str = ""

    img_url  = get_image_url(answer_raw, subject) if answer_raw else None
    song_url = get_song_url(answer_raw)           if answer_raw else None

    if img_url:
        if length_str:
            st.sidebar.markdown(
                f'<div style="font-size:2em;font-weight:bold;direction:rtl">{length_str}</div>',
                unsafe_allow_html=True,
            )
        st.sidebar.image(img_url, use_container_width=True)
        btn_key = f"open_img_{hash(answer_raw)}"
        if st.sidebar.button("🔍 פתח תמונה", key=btn_key):
            _open_image_anonymously(img_url)
    else:
        st.sidebar.markdown(
            f'<div style="font-size:2em;font-weight:bold;direction:rtl">{clue_text}</div>',
            unsafe_allow_html=True,
        )

    if song_url:
        st.sidebar.audio(song_url, format="audio/mp3")

def build_num_grid(placements):
    """
    בונה מילון: (r,c) → רשימת מספרי ההגדרות שמתחילות בתא זה.
    תא יכול להיות התחלה של הגדרה אופקית וגם אנכית בו-זמנית.
    """
    num_grid = {}
    for word, r, c, hor, num, orig_idx in placements:
        key = (r, c)
        if key not in num_grid:
            num_grid[key] = []
        num_grid[key].append(num)
    return num_grid


def grid_to_df(grid, placements):
    """
    ממיר את הרשת ל-DataFrame לתצוגה.
    תאי EMPTY → BLACK (" ", אדום).
    תאי אות → "" (לבן, ריק).
    תא ראשון של הגדרה → מספר/ים.
    """
    tmp = np.empty((GRID_SIZE, GRID_SIZE), dtype="<U10")
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            tmp[r, c] = BLACK if grid[r][c] == EMPTY else ""

    num_grid = build_num_grid(placements)
    for (r, c), nums in num_grid.items():
        # מיין ושמור את כל המספרים של התאים הראשונים
        label = "/".join(str(n) for n in sorted(nums))
        tmp[r, c] = label

    df = pd.DataFrame(tmp)
    return df


# ---------------------------------------------------------------------------
# לוגיקת הצבת תשובות
# ---------------------------------------------------------------------------
def hilight(s):
    return ["background-color: red" if ss == " " else "" for ss in s]


def slider_nums(clues_lst):
    nums = ["0"] + [str(i + 1) for i in range(len(clues_lst))]
    return nums


def get_placement_by_num(placements, num):
    for word, r, c, hor, n in placements:
        if n == num:
            return word, r, c, hor
    return None


def get_cell_letter(cell: str) -> str:
    """מחלץ את האות מתא שיכול להכיל גם מספר, למשל '9נ' → 'נ'."""
    return ''.join(c for c in cell if c.isalpha())


def get_cell_nums(cell: str) -> str:
    """מחלץ את חלק המספר מתא, למשל '9נ' → '9'."""
    return ''.join(c for c in cell if c.isdigit() or c == '/')


def is_word_filled(cross_df, word, r, c, hor) -> bool:
    """בדוק אם כל תאי המילה מכילים אות."""
    for i in range(len(word)):
        cell = cross_df.iloc[r, c + i] if hor else cross_df.iloc[r + i, c]
        if not get_cell_letter(cell):
            return False
    return True


def restore_numbers(cross_df, placements, num_grid):
    """
    לאחר הצבת תשובה:
    - תאים שהם תחילת הגדרה שטרם מולאה: מציג מספר+אות (אם יש אות) או מספר לבד.
    - תאים שכל הגדרותיהם מולאו: מציג אות בלבד.
    """
    for (r, c), nums in num_grid.items():
        cell = cross_df.iloc[r, c]
        letter = get_cell_letter(cell)

        # מצא מספרים של הגדרות שטרם מולאו
        active_nums = []
        for num in nums:
            # מצא את המילה המתאימה
            for p_word, pr, pc, p_hor, p_num, _ in placements:
                if p_num == num and pr == r and pc == c:
                    if not is_word_filled(cross_df, p_word, r, c, p_hor):
                        active_nums.append(num)
                    break

        if active_nums:
            nums_str = "/".join(str(n) for n in sorted(active_nums))
            cross_df.iloc[r, c] = nums_str + letter  # e.g. "9נ" or "9/12נ"
        elif letter:
            cross_df.iloc[r, c] = letter  # רק אות, הגדרות מולאו
    return cross_df


def on_ans(ans, word, r, c, hor, placements, num_grid):
    """מציב תשובה על הרשת ומשחזר מספרים לתאים שלא מולאו."""
    norm = normalize_answer(ans)
    expected = len(word)
    if len(norm) != expected:
        st.error(f"אורך שגוי: הקלדת {len(norm)} אותיות, נדרש {expected}", icon="🚨")
        return
    cross = st.session_state.cross
    for i, ch in enumerate(norm):
        if hor:
            cr, cc = r, c + i
        else:
            cr, cc = r + i, c
        existing = cross.iloc[cr, cc]
        nums_str = get_cell_nums(existing)
        # שמור מספר אם קיים, הוסף אות
        cross.iloc[cr, cc] = nums_str + ch if nums_str else ch
    # עדכן מספרים לפי מה שמולא
    cross = restore_numbers(cross, placements, num_grid)
    st.session_state.cross = cross


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    to_hebrew()
    set_bg("https://iris-bs.co.il/wp-content/uploads/2021/01/100111.jpg")

    init_firebase()

    # כותרת קשת דינמית לפי הנושא שנבחר
    def rainbow_title(text):
        colors = ["#e60000","#ff6600","#ffcc00","#33cc33","#0099ff","#6633cc","#cc33ff"]
        spans = "".join(
            f'<span style="color:{colors[i % len(colors)]}">{ch}</span>'
            for i, ch in enumerate(text)
        )
        st.markdown(
            f'<div style="text-align:center;font-size:2.5em;font-weight:bold;'
            f'border-bottom:4px solid #ccc;padding-bottom:6px;margin-bottom:16px">{spans}</div>',
            unsafe_allow_html=True,
        )

    # בחירת נושא בסייד-בר — חייב להיות לפני טעינת נתונים
    subjects = get_subjects()
    if not subjects:
        st.warning("לא נמצאו נושאים ב-Firebase.")
        return
    subject = st.sidebar.selectbox("בחר נושא תשבץ", subjects)
    if not subject:
        return

    rainbow_title(f"תשבץ {subject}")

    # טעינת הגדרות ופתרונות מ-Firebase
    pairs = get_words_from_firebase(subject)
    if not pairs:
        st.warning("לא נמצאו הגדרות לנושא זה.")
        return

    # Firebase: מפתח=הגדרה, ערך=פתרון → pairs=(פתרון_גולמי, הגדרה)
    answers_raw  = [p[0] for p in pairs]   # פתרון גולמי  e.g. "מתי כספי"
    hagdarot     = [p[1] for p in pairs]   # הגדרה לתצוגה e.g. "זמר ישראלי"
    # פתרון מנורמל: ללא רווחים, אותיות סופיות -> רגילות
    answers_norm = [normalize_answer(a) for a in answers_raw]
    # הגדרה + אורך לפי מילות הפתרון: "(4,5) זמר ישראלי"
    clues_with_len = [
        build_clue_with_length(hagdara, raw, norm)
        for hagdara, raw, norm in zip(hagdarot, answers_raw, answers_norm)
    ]

    # בנה תשבץ — מפתח כולל hash של הנתונים כדי שנתונים חדשים תמיד יבנו מחדש
    data_hash      = str(hash(tuple(sorted(answers_norm))))
    cache_key      = f"cross_state_{subject}_{data_hash}"
    placements_key = f"placements_{subject}_{data_hash}"
    numgrid_key    = f"num_grid_{subject}_{data_hash}"

    if cache_key not in st.session_state or st.session_state.get("current_subject") != subject:
        grid, placements = build_crossword(answers_norm)
        num_grid = build_num_grid(placements)
        df = grid_to_df(grid, placements)
        st.session_state[cache_key]      = df.copy()
        st.session_state[placements_key] = placements
        st.session_state[numgrid_key]    = num_grid
        st.session_state.cross           = df.copy()
        st.session_state["current_subject"] = subject
    else:
        # cache_key קיים — ודא שכל המפתחות הנלווים קיימים
        if placements_key not in st.session_state or numgrid_key not in st.session_state:
                grid, placements = build_crossword(answers_norm)
                num_grid = build_num_grid(placements)
                df = grid_to_df(grid, placements)
                st.session_state[cache_key]      = df.copy()
                st.session_state[placements_key] = placements
                st.session_state[numgrid_key]    = num_grid
                st.session_state.cross           = df.copy()

    if "cross" not in st.session_state:
        st.session_state.cross = st.session_state[cache_key].copy()

    placements = st.session_state[placements_key]
    num_grid   = st.session_state[numgrid_key]

    # --- Sidebar ---
    kivun = st.sidebar.radio("בחר כיוון", ["מאוזן", "מאונך"])
    st.sidebar.header(kivun)

    # פלטר הגדרות לפי כיוון
    if kivun == "מאוזן":
        direction_placements = [(w, r, c, hor, n, oi) for w, r, c, hor, n, oi in placements if hor]
    else:
        direction_placements = [(w, r, c, hor, n, oi) for w, r, c, hor, n, oi in placements if not hor]

    if not direction_placements:
        st.sidebar.warning("אין הגדרות בכיוון זה.")
    else:
        sorted_nums = [0] + sorted([p[4] for p in direction_placements])
        valid_strs  = [str(n) for n in sorted_nums]

        choose = st.sidebar.select_slider("בחר הגדרה", options=valid_strs, value="0")

        if choose != "0":
            # הצג מספר הגדרה בולט מעל ההגדרה
            st.sidebar.markdown(
                f'<div style="font-size:2em;font-weight:bold;color:#1a1a1a;text-align:right;margin-bottom:0">{choose}</div>',
                unsafe_allow_html=True,
            )

            chosen_placement = None
            for p in direction_placements:
                if p[4] == int(choose):
                    chosen_placement = p
                    break

            if chosen_placement:
                word, r, c, hor, num, orig_idx = chosen_placement
                clue_text = clues_with_len[orig_idx] if orig_idx < len(clues_with_len) else f"הגדרה {num}"
                answer_raw_for_clue = answers_raw[orig_idx] if orig_idx < len(answers_raw) else ""
                hagdara_raw_for_clue = hagdarot[orig_idx] if orig_idx < len(hagdarot) else ""

                display_clue_in_sidebar(
                    clue_text,
                    answer_raw=answer_raw_for_clue,
                    hagdara_raw=hagdara_raw_for_clue,
                    subject=subject,
                )

                ans = st.sidebar.text_input("פתרון")
                if st.sidebar.button("השב"):
                    on_ans(ans, word, r, c, hor, placements, num_grid)

    st.sidebar.button("רענן מסך")
    pitaronot = st.sidebar.checkbox("האם להציג פיתרונות?")

    if st.sidebar.button("אפס תשבץ"):
        if cache_key in st.session_state:
            st.session_state.cross = st.session_state[cache_key].copy()

    # --- הצגת הרשת ---
    col1, col2 = st.columns([10, 1])

    styled = st.session_state.cross.style.set_table_styles(
        [
            {
                "selector": "",
                "props": "color: blue;font-weight:bold;font-size:1.5em;border-style:solid;border-width:thick;",
            }
        ],
        overwrite=False,
    )
    styled = styled.apply(hilight).hide().hide(axis="columns")
    styled = styled.set_table_styles(
        [{"selector": "td", "props": "border-style:solid;border-width:thick;height:2em;width:2em;"}],
        overwrite=False,
    )

    col1.markdown(styled.to_html(), unsafe_allow_html=True)

    if pitaronot:
        col2.info(" | ".join(answers_norm))


if __name__ == "__main__":
    main()
