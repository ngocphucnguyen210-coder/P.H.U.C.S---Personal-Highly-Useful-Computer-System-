"""Optional service adapters for P.H.U.C.S AI.
All credentials are read from Streamlit secrets or environment variables.
"""
import os, base64, time, requests
from pathlib import Path


def setting(name, default=""):
    try:
        import streamlit as st
        value = st.secrets.get(name, None)
        if value is not None and str(value).strip():
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()


def tavily_search(query, max_results=5):
    key = setting("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("Thiếu TAVILY_API_KEY. Tạo khóa tại https://tavily.com/ rồi thêm vào Secrets.")
    r = requests.post("https://api.tavily.com/search", headers={"Authorization": f"Bearer {key}", "Content-Type":"application/json"},
                      json={"query": query, "max_results": max_results, "search_depth":"advanced", "include_answer":True}, timeout=45)
    r.raise_for_status()
    return r.json()


DEPRECATED_GROQ_MODELS = {
    "llama-3.3-70b-versatile": "openai/gpt-oss-120b",
    "llama-3.1-8b-instant": "openai/gpt-oss-20b",
    "meta-llama/llama-4-scout-17b-16e-instruct": "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b": "qwen/qwen3.8-27b",
}


def resolve_model(model, vision=False):
    """Normalize known retired Groq model IDs to currently documented alternatives."""
    model = (model or "").strip()
    if model in DEPRECATED_GROQ_MODELS:
        return DEPRECATED_GROQ_MODELS[model]
    if not model:
        return "qwen/qwen3.8-27b" if vision else "openai/gpt-oss-120b"
    return model


def ai_client(vision=False):
    from openai import OpenAI
    groq_key = setting("GROQ_API_KEY")
    openai_key = setting("OPENAI_API_KEY")
    if groq_key:
        model_setting = "GROQ_VISION_MODEL" if vision else "GROQ_MODEL"
        fallback = "qwen/qwen3.8-27b" if vision else "openai/gpt-oss-120b"
        model = resolve_model(setting(model_setting, fallback), vision=vision)
        client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1", timeout=60.0, max_retries=2)
        return client, model
    if openai_key:
        model = setting("OPENAI_VISION_MODEL" if vision else "OPENAI_MODEL", "gpt-4.1-mini")
        client = OpenAI(api_key=openai_key, timeout=60.0, max_retries=2)
        return client, model
    raise RuntimeError("Thiếu GROQ_API_KEY hoặc OPENAI_API_KEY trong Streamlit Secrets.")


def chat_completion(messages, max_completion_tokens=2048):
    """Create a chat completion and retry once with a supported Groq model if a retired ID is rejected."""
    client, model = ai_client(vision=False)
    is_groq = bool(setting("GROQ_API_KEY"))
    try:
        response = client.chat.completions.create(
            model=model, messages=messages, max_completion_tokens=max_completion_tokens
        )
        return response, model
    except Exception as exc:
        status = getattr(exc, "status_code", None)
        detail = str(exc).lower()
        looks_like_model_error = any(term in detail for term in (
            "model_not_found", "model not found", "decommissioned", "deprecated model",
            "model is not available", "model does not exist", "unsupported model"
        ))
        if is_groq and model != "openai/gpt-oss-120b" and (status in (400, 404) or looks_like_model_error) and looks_like_model_error:
            fallback = "openai/gpt-oss-120b"
            response = client.chat.completions.create(
                model=fallback, messages=messages, max_completion_tokens=max_completion_tokens
            )
            return response, fallback
        raise


def test_ai_connection():
    """Small live check for the configured text model; never prints or returns the API key."""
    response, model = chat_completion(
        [{"role": "user", "content": "Trả lời ngắn gọn bằng tiếng Việt: P.H.U.C.S đã kết nối AI thành công."}],
        max_completion_tokens=512,
    )
    text = response.choices[0].message.content or "API phản hồi nhưng không có nội dung văn bản."
    return model, text


def analyze_image(image_bytes, mime_type, question):
    client, model = ai_client(vision=True)
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":"Bạn là P.H.U.C.S, phân tích ảnh cẩn thận. Với bài tập, giải từng bước. Nếu ảnh mờ hoặc thiếu dữ kiện, hãy nói rõ; không đoán nội dung không nhìn thấy."},
                  {"role":"user","content":[{"type":"text","text":question or "Hãy mô tả và phân tích ảnh này."},
                                               {"type":"image_url","image_url":{"url":f"data:{mime_type};base64,{encoded}"}}]}],
        temperature=0.2)
    return response.choices[0].message.content


def transcribe_audio(audio_bytes, filename="recording.wav"):
    key = setting("GROQ_API_KEY")
    if key:
        from openai import OpenAI
        client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
        model = setting("GROQ_TRANSCRIPTION_MODEL", "whisper-large-v3-turbo")
    elif setting("OPENAI_API_KEY"):
        from openai import OpenAI
        client = OpenAI(api_key=setting("OPENAI_API_KEY"))
        model = setting("OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe")
    else:
        raise RuntimeError("Cần GROQ_API_KEY hoặc OPENAI_API_KEY để chuyển giọng nói thành văn bản.")
    import io
    return client.audio.transcriptions.create(model=model, file=(filename, io.BytesIO(audio_bytes))).text


def generate_image(prompt):
    key = setting("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Tạo ảnh hiện dùng OpenAI Images API. Hãy thêm OPENAI_API_KEY; Groq chỉ dùng cho chat/một số tác vụ khác.")
    from openai import OpenAI
    client = OpenAI(api_key=key)
    model = setting("OPENAI_IMAGE_MODEL", "gpt-image-1")
    result = client.images.generate(model=model, prompt=prompt, size="1024x1024")
    item = result.data[0]
    if getattr(item, "b64_json", None):
        return base64.b64decode(item.b64_json)
    if getattr(item, "url", None):
        img = requests.get(item.url, timeout=90); img.raise_for_status(); return img.content
    raise RuntimeError("Nhà cung cấp không trả về dữ liệu ảnh.")


def replicate_create(model, prompt, extra_input=None):
    """Create a Replicate prediction and poll briefly for a finished result.

    MODEL may be `owner/model` or `owner/model:version_id`. Long-running jobs
    can still return `starting`/`processing`; the UI should expose the prediction URL.
    """
    token = setting("REPLICATE_API_TOKEN")
    if not token:
        raise RuntimeError("Thiếu REPLICATE_API_TOKEN. Tạo token tại https://replicate.com/account/api-tokens.")
    if not model or "/" not in model:
        raise RuntimeError("Hãy đặt REPLICATE_VIDEO_MODEL hoặc REPLICATE_MUSIC_MODEL theo dạng owner/model hoặc owner/model:version_id.")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Prefer": "wait=20"}
    owner_model, sep, version = model.partition(":")
    inputs = {"prompt": prompt}
    if extra_input:
        inputs.update(extra_input)
    if sep and version:
        url = "https://api.replicate.com/v1/predictions"
        payload = {"version": version, "input": inputs}
    else:
        url = f"https://api.replicate.com/v1/models/{owner_model}/predictions"
        payload = {"input": inputs}
    r = requests.post(url, headers=headers, json=payload, timeout=90)
    if r.status_code == 404 and sep and version:
        # Some model endpoints require owner/model rather than a bare version endpoint.
        r = requests.post(f"https://api.replicate.com/v1/models/{owner_model}/predictions", headers=headers, json={"version": version, "input": inputs}, timeout=90)
    r.raise_for_status()
    data = r.json()
    # Prefer wait can return early on slow models. Poll for a short bounded period.
    deadline = time.time() + 45
    while data.get("status") in ("starting", "processing") and data.get("urls", {}).get("get") and time.time() < deadline:
        time.sleep(3)
        poll = requests.get(data["urls"]["get"], headers={"Authorization": f"Bearer {token}"}, timeout=30)
        poll.raise_for_status()
        data = poll.json()
    if data.get("status") == "failed":
        raise RuntimeError("Replicate báo tác vụ thất bại: " + str(data.get("error") or "không có chi tiết"))
    return data


def supabase_client():
    """Return the session's authenticated Supabase client when available, else anon client."""
    try:
        import streamlit as st
        existing = st.session_state.get("supabase_oauth_client")
        if existing is not None:
            return existing
    except Exception:
        pass
    url = setting("SUPABASE_URL")
    key = setting("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Cần SUPABASE_URL và SUPABASE_ANON_KEY. Chỉ dùng SUPABASE_SERVICE_ROLE_KEY trong máy chủ tin cậy, không dùng cho OAuth trên app.")
    from supabase import create_client
    return create_client(url, key)


def create_checkout_url(user_id, email=""):
    import stripe
    stripe.api_key = setting("STRIPE_SECRET_KEY")
    price_id = setting("STRIPE_PLUS_PRICE_ID")
    if not stripe.api_key or not price_id:
        raise RuntimeError("Cần STRIPE_SECRET_KEY và STRIPE_PLUS_PRICE_ID; tạo sản phẩm/giá trong Stripe Dashboard trước.")
    app_url = setting("APP_BASE_URL", "http://localhost:8501").rstrip("/")
    session = stripe.checkout.Session.create(
        mode="subscription", line_items=[{"price":price_id,"quantity":1}],
        success_url=app_url + "?payment=success", cancel_url=app_url + "?payment=cancelled",
        client_reference_id=str(user_id), customer_email=email or None,
        metadata={"phucs_user_id":str(user_id), "plan":"plus"},
        subscription_data={"metadata":{"phucs_user_id":str(user_id), "plan":"plus"}})
    return session.url


def upload_supabase_file(user_id, uploaded_file, bucket=None):
    client = supabase_client()
    bucket = bucket or setting("SUPABASE_STORAGE_BUCKET", "phucs-files")
    safe_name = Path(uploaded_file.name).name.replace(" ", "_")
    path = f"{user_id}/{int(time.time())}_{safe_name}"
    data = uploaded_file.getvalue()
    client.storage.from_(bucket).upload(path, data, {"content-type": uploaded_file.type or "application/octet-stream", "upsert":"false"})
    return {"bucket":bucket,"path":path,"size":len(data)}


def group_messages(group_id, limit=50):
    client = supabase_client()
    return client.table("group_messages").select("id,group_id,user_id,display_name,content,created_at").eq("group_id", group_id).order("created_at", desc=False).limit(limit).execute().data


def send_group_message(group_id, user_id, display_name, content):
    client = supabase_client()
    return client.table("group_messages").insert({"group_id":group_id,"user_id":str(user_id),"display_name":display_name,"content":content}).execute().data
