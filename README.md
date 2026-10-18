[README.md](https://github.com/user-attachments/files/33630579/README.md)
# P.H.U.C.S AI — AlphaOS 2 (Streamlit + Groq)

**P.H.U.C.S — Personal Highly Useful Computer System**  
Slogan: **“Đồng hành cùng P.H.U.C.S, vững bước thành công”**

Bộ mã nguồn này là một starter app có các phần hoạt động khi đã cấu hình dịch vụ phù hợp. Chat AI mặc định dùng `openai/gpt-oss-120b`; nếu Secrets còn chứa một số model Groq đã nghỉ, app sẽ tự chuẩn hóa sang model thay thế đã định nghĩa và có nút kiểm tra kết nối AI. Nó không thể tự tạo API key, tài khoản OAuth, dung lượng lưu trữ hoặc dịch vụ trả phí. Không đưa API key vào GitHub.

## Giao diện pastel hồng P.H.U.C.S

Bản này làm mới CSS theo phong cách hồng pastel: nền mộng mơ, thẻ bo tròn, nút gradient hồng, thanh điều hướng dạng viên thuốc và banner chào mừng. Các tab/chức năng, đăng nhập khách, lịch sử chat, học tập, ghi chú, biểu đồ, phòng thí nghiệm và tích hợp AI vẫn giữ trong `app.py`. Do Streamlit có bố cục riêng, đây là bản dựng gần sát tinh thần mockup, không phải bản sao pixel-perfect của ảnh thiết kế.

## 1. Chạy trên Streamlit Community Cloud

Xem thêm hướng dẫn triển khai từng bước bằng tiếng Việt trong `DEPLOY_QUICKSTART_VI.md`.

1. Giải nén ZIP.
2. Đưa **toàn bộ nội dung** thư mục `phucs_ai_starter` lên thư mục gốc của repository GitHub. Giữ nguyên `assets/phucs_logo.png` và `.streamlit/config.toml`.
3. Vào https://share.streamlit.io/ → New app → chọn repository → chọn `app.py`.
4. Vào App settings → Secrets và thêm các biến cần thiết ở mục dưới.
5. Save rồi khởi động lại app.

## 2. Secrets tối thiểu: chat + đọc ảnh + chuyển giọng nói thành chữ

```toml
GROQ_API_KEY = "gsk_THAY_BANG_KHOA_THAT"
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_VISION_MODEL = "qwen/qwen3.8-27b"
GROQ_TRANSCRIPTION_MODEL = "whisper-large-v3-turbo"
```

Lấy API key tại https://console.groq.com/keys. Model có thể thay đổi theo thời gian và quyền của tài khoản; kiểm tra danh sách model hiện hành tại https://console.groq.com/docs/models. Các model ở trên được chọn theo tài liệu Groq hiện hành khi tạo bản này. Vision cần model nhận ảnh; model chat văn bản không tự đọc được ảnh.

## 3. Các tích hợp tùy chọn

### Tìm kiếm Internet có nguồn

```toml
TAVILY_API_KEY = "tvly-THAY_BANG_KHOA_THAT"
```

Tạo key tại https://app.tavily.com/. Trong tab **Cơ bản**, bật checkbox “Tra cứu Internet và đính kèm nguồn khi trả lời”. Kết quả tìm kiếm có thể chưa đầy đủ hoặc lỗi thời; hãy mở nguồn gốc để xác minh.

### Tạo ảnh (OpenAI Images API)

```toml
OPENAI_API_KEY = "sk-THAY_BANG_KHOA_THAT"
OPENAI_IMAGE_MODEL = "gpt-image-1"
```

Tạo key tại https://platform.openai.com/api-keys. Groq API key không tự bật tạo ảnh OpenAI; OpenAI API được tính phí riêng.

### Tạo video và nhạc (Replicate)

```toml
REPLICATE_API_TOKEN = "r8_THAY_BANG_KHOA_THAT"
REPLICATE_VIDEO_MODEL = "owner/model"
REPLICATE_MUSIC_MODEL = "owner/model"
```

Tạo token tại https://replicate.com/account/api-tokens. Thay `owner/model` bằng model thật đang hoạt động và có schema đầu vào tương thích với `prompt`. Model cộng đồng có thể yêu cầu `owner/model:version_id`. Tác vụ video/nhạc có thể chạy lâu và phát sinh chi phí; app chờ trong thời gian giới hạn, sau đó hiển thị trạng thái/URL prediction nếu tác vụ chưa xong.

### Đăng nhập Google/Facebook/Apple và lưu trữ đám mây

```toml
SUPABASE_URL = "https://PROJECT_ID.supabase.co"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"
SUPABASE_STORAGE_BUCKET = "phucs-files"
APP_BASE_URL = "https://YOUR-APP.streamlit.app"
```

Tạo project tại https://supabase.com/dashboard. Bật OAuth từng provider, thêm URL callback/redirect đúng trong Supabase và trang developer tương ứng. Với Apple, cần cấu hình Apple Developer; đây không chỉ là nút liên kết.

Chạy `supabase_schema.sql` trong Supabase SQL Editor. Tạo bucket `phucs-files` và Storage policies. Các chính sách mẫu cần được rà soát trước khi mở công khai. Dùng `SUPABASE_SERVICE_ROLE_KEY` **chỉ ở máy chủ tin cậy** (ví dụ webhook riêng); tuyệt đối không đưa khóa service-role vào frontend hoặc GitHub.

Nếu Supabase chưa cấu hình, ứng dụng cung cấp chat nhóm cục bộ và lưu file tạm trong thư mục `data/uploads`. Đây không phải kho đám mây bền vững; file SQLite và file cục bộ có thể mất khi Streamlit Cloud khởi động lại.

### P.H.U.C.S Plus (Stripe)

```toml
STRIPE_SECRET_KEY = "sk_test_..."
STRIPE_PLUS_PRICE_ID = "price_..."
STRIPE_WEBHOOK_SECRET = "whsec_..."
```

Tạo sản phẩm/giá recurring trong https://dashboard.stripe.com/. Tạo endpoint webhook trỏ tới `/stripe/webhook` của `api_server.py`, rồi triển khai API riêng (ví dụ máy chủ Python hỗ trợ FastAPI). Cấu hình các biến Stripe và `SUPABASE_SERVICE_ROLE_KEY` trong **môi trường máy chủ webhook**, không chỉ trong Streamlit Secrets. Dùng Stripe test mode trước. Bản starter tạo checkout session và có webhook lưu trạng thái subscription; cần kiểm thử toàn bộ luồng trước khi thu tiền thật.

Giá 35.000 VNĐ/năm và mục tiêu 400–500 GB là cấu hình sản phẩm do chủ ứng dụng quyết định. Code không tự cấp dung lượng, không mua gói lưu trữ và không tự đảm bảo quyền lợi Plus nếu backend/billing chưa triển khai đầy đủ.

## 4. Tính năng trong bản này

- Logo mới trong `assets/phucs_logo.png`, trang đăng nhập, tài khoản khách và các nút OAuth (khi Supabase đã cấu hình).
- Chat Groq/OpenAI, lịch sử chat, xóa lịch sử, đính kèm ảnh để gọi vision, tìm web có link nguồn.
- Voice: ghi âm và speech-to-text qua Groq/OpenAI; text-to-speech dùng giọng đọc có sẵn của trình duyệt.
- Tạo ảnh qua OpenAI; tạo video/nhạc qua Replicate khi có token/model phù hợp.
- Đồng hồ học tự làm mới mỗi giây, lưu phiên học, lịch, sự kiện, todo.
- Note với Quill (nếu cài được), toolbar định dạng, màu chữ/highlight/chỉ số trên/dưới, ký hiệu học thuật; canvas có bút, cọ, bút kim, highlight, tẩy, hình cơ bản, đường nét đứt và tải PNG.
- Biểu đồ cột, thanh ngang, đường, miền và tròn/quạt.
- 30 mô phỏng học tập khái niệm; góc trò chơi có 30+ lựa chọn, trong đó các trò chưa có luật riêng dùng câu đố tương tác mẫu.
- Chat nhóm local fallback, Supabase group messages khi quyền xác thực đã cấu hình, phòng họp Jitsi bên ngoài.
- Upload file cloud qua Supabase Storage; local fallback chỉ để thử nghiệm.

## 5. Kiểm thử và giới hạn quan trọng

- Đã kiểm tra cú pháp Python của `app.py`, `phucs_integrations.py`, `api_server.py` khi đóng gói và chạy các kiểm thử offline cho cấu hình model.
- Chưa thể kiểm thử cuộc gọi AI thật trong môi trường đóng gói vì không sử dụng khóa API của người dùng; hãy chạy nút **Kiểm tra kết nối AI** sau khi đặt khóa riêng trong Secrets.
- Không thể xác minh API thật nếu không có khóa/tài khoản của chủ dự án. Sau khi triển khai, mở **Manage app → Logs** để đọc traceback khi một dịch vụ gặp lỗi.
- Không có AI nào đảm bảo trả lời đúng tuyệt đối mọi câu hỏi. Với bài học, đối chiếu sách/giáo viên/nguồn gốc; với y tế, pháp luật hoặc tài chính, dùng câu trả lời như thông tin tham khảo và hỏi chuyên gia khi cần.
- Đăng nhập OAuth, thanh toán, storage và group chat phải được cấu hình bảo mật trước khi dùng cho người thật. SQLite trên Streamlit Cloud không phải cơ sở dữ liệu sản xuất bền vững.

## 6. Chạy trên máy cá nhân

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
streamlit run app.py
```

Tạo `.env` từ `.env.example` cho local development. Không commit `.env`.
