    with st.form("event_form", clear_on_submit=True):
        ev_title = st.text_input("Tên sự kiện")
        ev_cat = st.selectbox("Phân loại", ["Sinh nhật", "Kỷ niệm", "Thi cử", "Quan trọng", "Khác"])
        ev_date = st.date_input("Ngày diễn ra", value=chosen_date, format="DD/MM/YYYY")
        ev_submit = st.form_submit_button("＋ Thêm sự kiện", type="primary")
    if ev_submit:
        if ev_title.strip():
            with db() as con:
                con.execute("INSERT INTO events(user_id,title,category,event_date) VALUES(?,?,?,?)",
                            (uid, ev_title.strip(), ev_cat, ev_date.isoformat()))
            st.success("Đã thêm sự kiện.")
            st.rerun()
        else:
            st.error("Hãy nhập tên sự kiện.")
    with db() as con:
        events = con.execute("SELECT id,title,category FROM events WHERE user_id=? AND event_date=? ORDER BY id",
                             (uid, chosen_date.isoformat())).fetchall()
    st.markdown(f"#### Sự kiện ngày {chosen_date.strftime('%d/%m/%Y')}")
    if not events:
        st.info("Không có sự kiện trong ngày này.")
    for ev in events:
        c1,c2 = st.columns([5,1])
        c1.write(f"**{ev['title']}** · {ev['category']}")
        if c2.button("Xóa", key=f"del_ev_{ev['id']}"):
            with db() as con: con.execute("DELETE FROM events WHERE id=? AND user_id=?", (ev["id"],uid))
            st.rerun()

# ---------- Todo ----------
with pages[3]:
    st.subheader("✅ To-do List")
    todo_date = st.date_input("Ngày thực hiện", value=date.today(), format="DD/MM/YYYY", key="todo_date")
    with st.form("todo_form", clear_on_submit=True):
        task = st.text_input("Nhiệm vụ mới", placeholder="Ví dụ: Ôn 20 từ vựng IELTS")
        add_task = st.form_submit_button("＋ Thêm nhiệm vụ", type="primary")
    if add_task and task.strip():
        with db() as con:
            con.execute("INSERT INTO todos(user_id,task,due_date,done) VALUES(?,?,?,0)",
                        (uid,task.strip(),todo_date.isoformat()))
        st.rerun()
    with db() as con:
        todos = con.execute("SELECT id,task,done FROM todos WHERE user_id=? AND due_date=? ORDER BY done,id",
                            (uid,todo_date.isoformat())).fetchall()
    st.markdown("#### Chưa hoàn thành")
    for t in [x for x in todos if not x["done"]]:
        c1,c2 = st.columns([6,1])
        c1.write("✕ " + t["task"])
        if c2.button("✓", key=f"done_{t['id']}"):
            with db() as con: con.execute("UPDATE todos SET done=1 WHERE id=? AND user_id=?", (t["id"],uid))
            st.rerun()
    st.markdown("#### Đã hoàn thành")
    for t in [x for x in todos if x["done"]]:
        c1,c2 = st.columns([6,1])
        c1.markdown(f"~~{t['task']}~~")
        if c2.button("↩", key=f"undo_{t['id']}"):
            with db() as con: con.execute("UPDATE todos SET done=0 WHERE id=? AND user_id=?", (t["id"],uid))
            st.rerun()
    if not todos:
        st.info("Chưa có nhiệm vụ nào trong ngày này.")

# ---------- Notes and drawing ----------
with pages[4]:
    st.subheader("📝 Note & Studio Pro")
    mode = st.radio("Chế độ", ["Trình soạn thảo văn bản", "Bảng vẽ Studio Pro"], horizontal=True)
    if mode == "Trình soạn thảo văn bản":
        note_title = st.text_input("Tiêu đề ghi chú", key="rich_note_title")
        st.caption("Trình soạn thảo hỗ trợ định dạng văn bản, phông chữ, màu chữ, highlight, danh sách và ký hiệu học thuật nếu streamlit-quill được cài.")
        editor_html = ""
        try:
            from streamlit_quill import st_quill
            toolbar = [[{"font": []}, {"size": ["small", False, "large", "huge"]}],
                       ["bold", "italic", "underline", "strike"],
                       [{"color": []}, {"background": []}],
                       [{"script": "sub"}, {"script": "super"}],
                       [{"header": [1, 2, 3, False]}],
                       [{"list": "ordered"}, {"list": "bullet"}],
                       [{"align": []}], ["blockquote", "code-block", "link"], ["clean"]]
            editor_html = st_quill(placeholder="Soạn ghi chú, công thức, bài học...", html=True, toolbar=toolbar, key="rich_note_editor") or ""
        except Exception:
            st.warning("Trình soạn thảo nâng cao chưa tải được; đang dùng chế độ văn bản cơ bản. Kiểm tra streamlit-quill trong requirements.txt.")
            editor_html = st.text_area("Nội dung ghi chú", height=260, placeholder="Có thể nhập công thức: H₂O, v = s/t, x², ∑, √, π, Δ, →, ⇌, °C...", key="basic_note_body")
        with st.expander("∑ Ký hiệu Toán – Lý – Hóa – Sinh"):
            symbols = ["α", "β", "γ", "Δ", "θ", "λ", "μ", "π", "Σ", "Ω", "√", "∛", "∞", "≈", "≠", "≤", "≥", "±", "×", "÷", "∑", "∫", "∂", "∇", "→", "⇌", "°", "℃", "m/s", "mol", "H₂O", "CO₂", "Na⁺", "SO₄²⁻", "x²", "x₁", "Fe³⁺", "DNA", "RNA"]
            st.write("　".join(f"`{x}`" for x in symbols))
            st.caption("Có thể sao chép ký hiệu ở trên và dán vào ghi chú. Với Quill, dùng các nút sub/super để định dạng chỉ số.")
        if st.button("💾 Lưu ghi chú", type="primary", key="save_rich_note"):
            if note_title.strip() and str(editor_html).strip():
                with db() as con:
                    con.execute("INSERT INTO notes(user_id,title,body,created_at) VALUES(?,?,?,?)", (uid, note_title.strip(), str(editor_html), datetime.now().isoformat(timespec="seconds")))
                st.success("Đã lưu ghi chú.")
                st.rerun()
            else:
                st.error("Vui lòng nhập tiêu đề và nội dung.")
    else:
        st.caption("Studio Pro: bút bi, bút cọ, bút kim, highlight, tẩy, đường liền/nét đứt, hình chữ nhật, hình tròn, tam giác và tải PNG.")
        st.components.v1.html(r"""<!doctype html><html><head><style>
        body{font-family:Arial;background:#fff4f8;margin:0;padding:10px;color:#74314f} .toolbar{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:9px;align-items:center}
        button,select{border:1px solid #e8a7c2;background:white;border-radius:8px;padding:7px;color:#74314f;font-weight:600} canvas{display:block;width:100%;height:auto;background:#fff;border:1px solid #e8a7c2;border-radius:12px;touch-action:none}
        </style></head><body><div class="toolbar">
        <select id="tool"><option value="pen">Bút bi</option><option value="brush">Bút cọ</option><option value="fine">Bút kim</option><option value="highlighter">Highlight</option><option value="eraser">Tẩy</option><option value="line">Đường thẳng liền</option><option value="dashed">Đường nét đứt</option><option value="rect">Hình chữ nhật</option><option value="circle">Hình tròn</option><option value="triangle">Tam giác</option></select>
        <label>Màu <input id="color" type="color" value="#d94f83"></label><label>Nét <input id="width" type="range" min="1" max="30" value="4"></label>
        <button id="undo">↶ Hoàn tác</button><button id="clear">🗑 Tẩy hết</button><button id="download">⬇ Tải PNG</button></div>
        <canvas id="pad" width="1200" height="620"></canvas><script>
        const c=document.getElementById('pad'),ctx=c.getContext('2d');ctx.lineCap='round';ctx.lineJoin='round';ctx.fillStyle='#fff';ctx.fillRect(0,0,c.width,c.height);let down=false,start=null,last=null,history=[];
        function save(){history.push(ctx.getImageData(0,0,c.width,c.height));if(history.length>30)history.shift()} save();
        function pos(e){let r=c.getBoundingClientRect();return{x:(e.clientX-r.left)*c.width/r.width,y:(e.clientY-r.top)*c.height/r.height}}
        function style(){let t=document.getElementById('tool').value;ctx.globalCompositeOperation=t==='eraser'?'destination-out':'source-over';ctx.strokeStyle=document.getElementById('color').value;ctx.lineWidth=+document.getElementById('width').value;ctx.globalAlpha=t==='highlighter'?.24:1;if(t==='brush')ctx.lineWidth*=2.5;if(t==='fine')ctx.lineWidth=Math.min(ctx.lineWidth,2);ctx.setLineDash(t==='dashed'?[12,8]:[])}
        function shape(a,b,t){style();ctx.beginPath();if(t==='line'||t==='dashed'){ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y)}else if(t==='rect'){ctx.rect(a.x,a.y,b.x-a.x,b.y-a.y)}else if(t==='circle'){let r=Math.hypot(b.x-a.x,b.y-a.y);ctx.arc(a.x,a.y,r,0,Math.PI*2)}else if(t==='triangle'){ctx.moveTo((a.x+b.x)/2,a.y);ctx.lineTo(a.x,b.y);ctx.lineTo(b.x,b.y);ctx.closePath()}ctx.stroke();ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';ctx.setLineDash([])}
        c.addEventListener('pointerdown',e=>{save();down=true;start=last=pos(e);c.setPointerCapture(e.pointerId);if(['line','dashed','rect','circle','triangle'].includes(document.getElementById('tool').value)){} });
        c.addEventListener('pointermove',e=>{if(!down)return;let p=pos(e),t=document.getElementById('tool').value;if(['line','dashed','rect','circle','triangle'].includes(t)){let snap=history[history.length-1];ctx.putImageData(snap,0,0);shape(start,p,t)}else{style();ctx.beginPath();ctx.moveTo(last.x,last.y);ctx.lineTo(p.x,p.y);ctx.stroke();ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';last=p}});
        c.addEventListener('pointerup',()=>{down=false;start=last=null;ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';ctx.setLineDash([])});
        document.getElementById('clear').onclick=()=>{save();ctx.clearRect(0,0,c.width,c.height);ctx.fillStyle='#fff';ctx.fillRect(0,0,c.width,c.height)};
        document.getElementById('undo').onclick=()=>{if(history.length>1){history.pop();ctx.putImageData(history[history.length-1],0,0)}};
        document.getElementById('download').onclick=()=>{let a=document.createElement('a');a.download='phucs-studio.png';a.href=c.toDataURL('image/png');a.click()};
        </script></body></html>""", height=720, scrolling=True)
    st.markdown("#### Kho lưu trữ ghi chú")
    with db() as con:
        notes = con.execute("SELECT id,title,body,created_at FROM notes WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    if not notes:
        st.caption("Chưa có ghi chú được lưu.")
    for n in notes:
        with st.expander(f"🗒️ {n['title']} · {n['created_at'][:10]}"):
            # Render only a small allowlist of formatting tags saved by the rich-text editor.
            try:
                import bleach
                safe_html = bleach.clean(n['body'], tags=['p','br','strong','b','em','i','u','s','ol','ul','li','h1','h2','h3','blockquote','pre','code','span','div','sub','sup','a'], attributes={'a':['href','target'], 'span':['style'], 'div':['style']}, protocols=['http','https','mailto'])
                st.markdown(safe_html, unsafe_allow_html=True)
            except Exception:
                st.text(n['body'])
            if st.button("Xóa ghi chú", key=f"delete_note_{n['id']}"):
                with db() as con: con.execute("DELETE FROM notes WHERE id=? AND user_id=?", (n['id'],uid))
                st.rerun()

# ---------- Charts ----------
with pages[5]:
    st.subheader("📊 Tạo biểu đồ")
    st.caption("Nhập dữ liệu theo từng dòng, mỗi dòng gồm nhãn và giá trị, phân cách bằng dấu phẩy.")
    chart_type = st.selectbox("Loại biểu đồ", ["Biểu đồ cột dọc", "Biểu đồ thanh ngang", "Biểu đồ đường", "Biểu đồ miền", "Biểu đồ tròn / quạt"])
    data_text = st.text_area("Dữ liệu", value="Toán,8\nVăn,7\nTiếng Anh,9", height=120)
    if st.button("Vẽ biểu đồ", type="primary"):
        import pandas as pd
        rows = []
        for line in data_text.splitlines():
            try:
                label, value = line.rsplit(",",1)
                rows.append({"Mục":label.strip(),"Giá trị":float(value.strip())})
            except ValueError:
                pass
        if rows:
            frame = pd.DataFrame(rows).set_index("Mục")
            if chart_type == "Biểu đồ cột dọc": st.bar_chart(frame)
            elif chart_type == "Biểu đồ thanh ngang":
                try:
                    import plotly.express as px
                    fig = px.bar(pd.DataFrame(rows), x="Giá trị", y="Mục", orientation="h", color="Mục", title="Biểu đồ thanh ngang")
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    st.dataframe(pd.DataFrame(rows).sort_values("Giá trị"), use_container_width=True)
                    st.caption("Cài plotly để hiển thị biểu đồ thanh ngang tương tác.")
            elif chart_type == "Biểu đồ đường": st.line_chart(frame)
            elif chart_type == "Biểu đồ miền": st.area_chart(frame)
