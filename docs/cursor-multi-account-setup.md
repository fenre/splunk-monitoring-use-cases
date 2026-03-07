# Run Two Cursor Sessions with Different Accounts (macOS)

Step-by-step for **Method 1**: duplicate Cursor and use separate data directories so each instance keeps its own login. Both instances can run at the same time.

---

## Overview

| Step | What you do |
|------|-------------|
| 1 | Quit Cursor completely |
| 2 | Duplicate Cursor.app and rename the copy |
| 3 | Create two pairs of data directories (user data + extensions) |
| 4 | Create two launch scripts that point each app to its directories |
| 5 | (Optional) Add shell aliases |
| 6 | (Optional) Create Dock launchers with Automator |
| 7 | Launch each instance once and log in with the correct account |

---

## 1. Quit Cursor

1. **Quit the app fully**  
   - Menu bar: **Cursor** → **Quit Cursor**, or press `Cmd+Q`.  
   - Don’t just close the window; the app must not be running.

2. **Confirm it’s closed**  
   - Open **Activity Monitor** (Spotlight → “Activity Monitor”).  
   - Search for “Cursor”.  
   - If any **Cursor** process appears, select it → **Quit** (or Force Quit).  
   - Repeat until no Cursor process is listed.

This avoids “app in use” or permission issues when duplicating the app.

---

## 2. Duplicate the Cursor app

1. **Open Applications**  
   - Finder → **Go** → **Applications** (or `Cmd+Shift+A`).

2. **Locate Cursor**  
   - Find **Cursor.app** in the list.  
   - If you use a different install path (e.g. from a .dmg or Homebrew), use that path in the scripts in step 4.

3. **Duplicate the app**  
   - Select **Cursor.app**.  
   - Right-click → **Duplicate** (or `Cmd+D`).  
   - A copy named **Cursor copy.app** (or **Cursor 2.app**) will appear.

4. **Rename the copy**  
   - Click the name once to edit, or right-click → **Rename**.  
   - Use a name that tells the two apart, e.g.:  
     - **Cursor Work.app** (for work account)  
     - **Cursor Personal.app** (for personal account)  
   - The **exact name** must match what you type in the launch scripts (including spaces).  
   - Leave the original as **Cursor.app** (this will be “Account A” in the steps below).

5. **Check both apps exist**  
   - You should see: **Cursor.app** and **Cursor Work.app** (or whatever you named the duplicate).  
   - Both must stay in **Applications** (or the same path you’ll use in the scripts).

---

## 3. Create separate data directories

Each instance needs its **own** user data and extensions so logins and settings don’t mix.

1. **Open Terminal**  
   - Spotlight → “Terminal”, or **Applications** → **Utilities** → **Terminal**.

2. **Create the directories** (copy and run as one block):

```zsh
# Account A (used with original Cursor.app)
mkdir -p ~/.cursor-account-a
mkdir -p ~/.cursor-account-a-ext

# Account B (used with the duplicate, e.g. Cursor Work.app)
mkdir -p ~/.cursor-account-b
mkdir -p ~/.cursor-account-b-ext
```

3. **Verify they were created**  
   Run:

```zsh
ls -la ~ | grep cursor
```

   You should see:

   - `.cursor-account-a`
   - `.cursor-account-a-ext`
   - `.cursor-account-b`
   - `.cursor-account-b-ext`

4. **Optional naming**  
   You can use different names (e.g. `~/.cursor-work` and `~/.cursor-work-ext`) as long as you use the **same** names in the scripts in step 4.

---

## 4. Create launch scripts (recommended)

Scripts ensure each app always starts with the correct data directories. Create two zsh scripts.

### 4a. Script for Account A (original Cursor.app)

1. **Create the script file**  
   In Terminal:

```zsh
vim ~/cursor-account-a.sh
```

2. **Paste this** (no changes needed if Cursor is in `/Applications`). In vim: press `i` to enter insert mode, paste the lines below, press `Esc`, then type `:wq` and Enter to save and exit.

```zsh
#!/bin/zsh
/Applications/Cursor.app/Contents/MacOS/Cursor \
  --user-data-dir="$HOME/.cursor-account-a" \
  --extensions-dir="$HOME/.cursor-account-a-ext" \
  "$@"
```

3. **Save and exit**  
   - Press `Esc`, then type `:wq` and Enter.

4. **Make it executable**:

```zsh
chmod +x ~/cursor-account-a.sh
```

5. **Quick test**  
   Run:

```zsh
~/cursor-account-a.sh
```

   Cursor should open. If you see a login screen or your usual workspace, the script works. You can quit Cursor for now.

### 4b. Script for Account B (duplicate app, e.g. Cursor Work.app)

1. **Create the second script**:

```zsh
vim ~/cursor-account-b.sh
```

2. **Paste this** — **replace `Cursor Work.app`** with the **exact** name of your duplicate (including spaces; the backslash before the space is required). In vim: press `i`, paste, press `Esc`, then type `:wq` and Enter to save and exit.

```zsh
#!/bin/zsh
/Applications/Cursor\ Work.app/Contents/MacOS/Cursor \
  --user-data-dir="$HOME/.cursor-account-b" \
  --extensions-dir="$HOME/.cursor-account-b-ext" \
  "$@"
```

   Examples:  
   - If the duplicate is **Cursor Personal.app**, use:  
     `/Applications/Cursor\ Personal.app/Contents/MacOS/Cursor`

3. **Save and exit**  
   - Press `Esc`, then type `:wq` and Enter.

4. **Make it executable**:

```zsh
chmod +x ~/cursor-account-b.sh
```

5. **Quick test**  
   Run:

```zsh
~/cursor-account-b.sh
```

   A **second** Cursor window should open (possibly with a fresh/welcome state). That’s the second instance. You can quit it for now.

---

## 5. (Optional) Add shell aliases

macOS uses **zsh** as the default shell. You can add short commands like `cursor-a` and `cursor-b`.

1. **Open your zsh config**:

```zsh
vim ~/.zshrc
```

   (If the file doesn’t exist, vim will create it when you save.)

2. **Add at the end of the file**. In vim: press `i` to enter insert mode, go to the end of the file (e.g. `G` then `o` for a new line), paste the lines below, press `Esc`, then type `:wq` and Enter to save and exit.

```zsh
# Cursor multi-account
alias cursor-a="$HOME/cursor-account-a.sh"
alias cursor-b="$HOME/cursor-account-b.sh"
```

3. **Save and exit**  
   - Press `Esc`, then type `:wq` and Enter.

4. **Reload the config**:

```zsh
source ~/.zshrc
```

5. **Use the aliases**  
   - **Account A:** `cursor-a`  
   - **Account B:** `cursor-b`  
   You can also keep using `~/cursor-account-a.sh` and `~/cursor-account-b.sh` if you prefer.

---

## 6. (Optional) Dock launchers via Automator

So you can start each instance from a Dock icon instead of the terminal.

### 6a. Launcher for Account B (e.g. “Cursor Work”)

1. **Open Automator**  
   Spotlight → “Automator”.

2. **New document**  
   - **File** → **New** (or `Cmd+N`).  
   - Choose **Application** → **Choose**.

3. **Add the shell action**  
   - In the left column, search for **Run Shell Script**.  
   - Double-click it so it appears on the right.

4. **Set “Pass input”**  
   - At the top of the action, set the dropdown to **to stdin** (or leave as “to input” if that’s the only option).

5. **Paste the script**  
   Replace the default “cat” with (adjust the app name if needed). Automator uses zsh by default on macOS:

```zsh
/Applications/Cursor\ Work.app/Contents/MacOS/Cursor \
  --user-data-dir="$HOME/.cursor-account-b" \
  --extensions-dir="$HOME/.cursor-account-b-ext"
```

6. **Save the app**  
   - **File** → **Save** (or `Cmd+S`).  
   - Name it e.g. **Cursor Work**.  
   - Where: **Applications**.  
   - File Format: **Application**.  
   - Click **Save**.

7. **Add to Dock**  
   - Open **Applications**, find **Cursor Work**.  
   - Drag **Cursor Work** to the Dock.  
   - Optional: right-click the Dock icon → **Options** → **Keep in Dock**.

### 6b. Launcher for Account A (e.g. “Cursor Personal” or “Cursor A”)

1. In Automator: **File** → **New** → **Application**.
2. Add **Run Shell Script** again (it runs with zsh on macOS).
3. Paste:

```zsh
/Applications/Cursor.app/Contents/MacOS/Cursor \
  --user-data-dir="$HOME/.cursor-account-a" \
  --extensions-dir="$HOME/.cursor-account-a-ext"
```

4. Save as e.g. **Cursor A** or **Cursor Personal** in **Applications**.
5. Drag that app to the Dock as well.

**Note:** The Automator app runs the command directly (with zsh); it does not use your `cursor-account-a.sh` script. The result is the same as long as the paths match.

---

## 7. First-time login per instance

1. **Start Account A**  
   - Run `~/cursor-account-a.sh` or `cursor-a` or the first Dock app.  
   - If the data dir is new, you’ll see sign-in or welcome.  
   - Log in with your **first** account (e.g. work).  
   - Install any extensions you want for this account.

2. **Start Account B**  
   - Run `~/cursor-account-b.sh` or `cursor-b` or the second Dock app.  
   - Log in with your **second** account (e.g. personal).  
   - Install extensions for this account if needed.

3. **Use both at once**  
   - You can leave both running. Each window uses its own account and data dir.  
   - Always start “Account A” with the Account A script/app and “Account B” with the Account B script/app so you don’t mix data dirs.

---

## 8. Quick reference

| Instance   | Script                | Alias     | Data dir (user)      | Data dir (extensions)   |
|-----------|------------------------|-----------|-----------------------|--------------------------|
| Account A | `~/cursor-account-a.sh` | `cursor-a` | `~/.cursor-account-a` | `~/.cursor-account-a-ext` |
| Account B | `~/cursor-account-b.sh` | `cursor-b` | `~/.cursor-account-b` | `~/.cursor-account-b-ext` |

**App paths (for scripts and Automator):**  
- Account A: `/Applications/Cursor.app/Contents/MacOS/Cursor`  
- Account B (if duplicate is **Cursor Work.app**): `/Applications/Cursor\ Work.app/Contents/MacOS/Cursor`  
  (Use the exact duplicate name; the backslash escapes the space in the path.)

---

## Troubleshooting

- **“Cursor is damaged” / Gatekeeper warning**  
  Duplicating the app can break code signing.  
  - Try: Remove the duplicate, duplicate **Cursor.app** again, then rename.  
  - Or use a signed duplicate from a tool like **Cursor Kit** if you use one.  
  - You can also right-click the duplicate → **Open** once to allow it in System Settings → Privacy & Security.

- **Both windows show the same account**  
  Both instances are using the same user data dir.  
  - Confirm you’re launching via the correct script or Dock app for each account.  
  - In the scripts, confirm `--user-data-dir` is different for each (e.g. `account-a` vs `account-b`).  
  - Don’t open Cursor from Spotlight or the original **Cursor.app** icon without the flags; that uses the default data dir.

- **Extensions missing in one instance**  
  Each instance uses its own `--extensions-dir`.  
  - Install extensions once per instance (Cursor → Settings → Extensions, or the Extensions view).  
  - Log in with the right account in that window so license/account-specific features match.

- **“Permission denied” when running the script**  
  The script isn’t executable. Run:  
  `chmod +x ~/cursor-account-a.sh` and `chmod +x ~/cursor-account-b.sh`.

- **Wrong Cursor opens from Dock**  
  The Automator app’s **Run Shell Script** must point to the correct `.app` path and the correct `--user-data-dir` / `--extensions-dir`. Open the Automator app, edit the script, fix the paths, and save.
