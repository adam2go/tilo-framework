# PR #47 — Auth Module Refactor

**Branch:** `feature/auth-refactor` → `main`
**Author:** dev-team
**Reviewers requested:** security-team, backend-lead

## Summary

Refactors the authentication module to use JWT tokens instead of session cookies. Extracts user lookup into a helper function and adds a `/me` endpoint.

---

## Diff

### `backend/auth/login.py` (modified)

```diff
-from flask import request, session, jsonify
+from flask import request, jsonify
+import jwt
+import datetime
+import logging
 from db import get_db

-SECRET_KEY = "supersecret"
+SECRET_KEY = os.getenv("JWT_SECRET", "fallback-secret-do-not-use-in-prod")

 @app.route("/login", methods=["POST"])
 def login():
     username = request.json.get("username")
     password = request.json.get("password")

-    query = f"SELECT * FROM users WHERE username = '{username}'"
+    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
     db = get_db()
     user = db.execute(query).fetchone()

     if not user:
         return jsonify({"error": "Invalid credentials"}), 401

-    session["user_id"] = user["id"]
-    return jsonify({"ok": True})
+    token = jwt.encode(
+        {"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
+        SECRET_KEY,
+        algorithm="HS256",
+    )
+    return jsonify({"token": token})
```

### `backend/auth/helpers.py` (new file)

```diff
+from db import get_db
+
+def get_user(user_id):
+    db = get_db()
+    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
+    posts = db.execute("SELECT * FROM posts WHERE author_id = ?", (user_id,)).fetchall()
+    comments = db.execute("SELECT * FROM comments WHERE user_id = ?", (user_id,)).fetchall()
+    return {"user": user, "posts": posts, "comments": comments}
```

### `backend/auth/routes.py` (new file)

```diff
+from flask import request, jsonify
+from helpers import get_user
+import jwt
+
+@app.route("/me", methods=["GET"])
+def me():
+    token = request.headers.get("Authorization", "").replace("Bearer ", "")
+    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
+    user_id = payload["user_id"]
+    return jsonify(get_user(user_id))
```

---

## Test coverage

- `tests/test_login.py` — happy path only (no edge cases added)
- No tests for `/me` endpoint

## Checklist

- [x] Manual testing on local dev
- [ ] Security review
- [ ] Rate limiting
- [ ] Input validation
