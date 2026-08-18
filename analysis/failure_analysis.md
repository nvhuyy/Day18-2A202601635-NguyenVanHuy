# Failure Analysis — Lab 18: Production RAG

**Nhóm:** Huy01635
**Thành viên:** Nguyễn Văn Huy — M1, M2, M3, M4; tích hợp M5
**Nguồn số liệu:** `reports/naive_baseline_report.json` và `reports/ragas_report.json` (20 câu hỏi)

## Kết quả RAGAS

| Metric | Naive baseline | Production | Δ (Production − Naive) | Diễn giải |
|---|---:|---:|---:|---|
| Faithfulness | 0.5817 | 0.7072 | +0.1256 | Câu trả lời production bám context tốt hơn; đây là cải thiện lớn nhất. |
| Answer relevancy | 0.0811 | 0.0798 | -0.0013 | Rất thấp ở cả hai pipeline; đây là nút thắt chính của khâu sinh câu trả lời. |
| Context precision | 0.8792 | 0.7583 | -0.1208 | Hybrid retrieval tăng độ bao phủ nhưng đưa thêm chunk nhiễu vào top-k. |
| Context recall | 0.7333 | 0.7375 | +0.0042 | Tăng nhẹ; vẫn cần cải thiện với câu có nhiều điều kiện hoặc nhiều tài liệu. |

Production đạt từ 0.70 ở 3/4 metric (faithfulness, context precision và context recall). Tuy nhiên, answer relevancy chỉ khoảng 0.08 nên không nên diễn giải kết quả này là pipeline đã trả lời tốt toàn diện: context thường có căn cứ, nhưng câu trả lời chưa tập trung đầy đủ vào yêu cầu của câu hỏi.

## Bottom-5 failures

Danh sách dưới đây giữ đúng thứ tự 5 failure đầu trong `reports/ragas_report.json`. Điểm “worst metric” là tín hiệu chẩn đoán do pipeline ghi lại; nguyên nhân gốc được đối chiếu thêm với corpus.

### #1 — Mua thiết bị trị giá 55 triệu

- **Question:** Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?
- **Expected:** Tổng Giám đốc (CEO), vì đơn hàng trên 50.000.000 VNĐ.
- **Observed:** `context_precision = 0.0000`; diagnostic: `Too many irrelevant chunks`.
- **Error tree:** Output chưa chắc đúng → context có đúng hàng “trên 50.000.000 VNĐ” trong bảng thẩm quyền? → không ổn định vì bảng có thể bị tách thành child chunks → lỗi chính là retrieval/ranking cho bảng và ngưỡng số.
- **Root cause:** `mua_sam.md` chứa bảng thẩm quyền và các quy trình khác có cùng từ “mua sắm”; child chunk ngắn có thể làm top-k lẫn nội dung không trả lời trực tiếp ngưỡng 55 triệu.
- **Suggested fix:** Giữ nguyên bảng trong structure-aware chunk; boost các thực thể số/tiền tệ và rerank top-10 trước khi chọn context cuối.

### #2 — Nghỉ không lương 20 ngày

- **Question:** Nghỉ phép không lương 20 ngày cần ai phê duyệt?
- **Expected:** CEO; đồng thời nghỉ trên 14 ngày phải tự đóng phần bảo hiểm của mình.
- **Observed:** `faithfulness = 0.0000`; diagnostic: `LLM hallucinating`.
- **Error tree:** Output không được context hỗ trợ → context có đủ quy tắc “16–30 ngày” và “trên 14 ngày” không? → câu hỏi cần hai điều kiện trong hai section → lỗi kết hợp retrieval và generation.
- **Root cause:** Child retrieval ưu tiên đoạn khớp “20 ngày” nhưng không bảo đảm lấy đủ parent/section chứa cả thẩm quyền và ảnh hưởng phúc lợi.
- **Suggested fix:** Khi child được chọn, mở rộng context sang parent section; prompt yêu cầu nêu điều kiện liên quan và chỉ trả lời điều được context chứng minh.

### #3 — Hoàn chi đào tạo 25 triệu

- **Question:** Nhân viên được tài trợ khóa học 25 triệu, nghỉ việc sau 8 tháng hoàn thành khóa học. Phải hoàn trả bao nhiêu?
- **Expected:** Hoàn trả 100% chi phí, tức 25.000.000 VNĐ.
- **Observed:** `answer_relevancy = 0.0461`; diagnostic: `Answer doesn't match question`.
- **Error tree:** Context có thể liên quan → câu trả lời đã thực hiện phép suy luận “100% × 25 triệu” và kết luận số tiền chưa? → chưa bảo đảm → lỗi chính là answer synthesis.
- **Root cause:** Câu hỏi ghép điều kiện thời hạn cam kết với phép tính số tiền; generator có thể lặp lại chính sách thay vì kết luận trực tiếp số phải hoàn trả.
- **Suggested fix:** Dùng prompt theo mẫu “kết luận → căn cứ → phép tính”; thêm regression test cho các câu hỏi cần suy luận số học đơn giản.

### #4 — Phát hiện malware

- **Question:** Khi phát hiện malware trên máy, nhân viên có nên tự xử lý không?
- **Expected:** Không; phải báo trong vòng 1 giờ qua helpdesk hoặc hotline CNTT.
- **Observed:** `faithfulness = 0.0000`; diagnostic: `LLM hallucinating`.
- **Error tree:** Câu trả lời không bám context → có retrieve đúng quy trình xử lý sự cố? → nếu có thì prompt/generation chưa ràng buộc chặt → lỗi chính là faithfulness/generation.
- **Root cause:** Đây là câu phủ định có hành động bắt buộc. Khi trả lời bằng đoạn context hoặc câu sinh tự do, pipeline dễ bỏ mất phủ định “không tự ý xử lý” hoặc thời hạn báo cáo.
- **Suggested fix:** Thêm hướng dẫn xử lý negation trong prompt (“giữ nguyên KHÔNG/CÓ”) và kiểm tra câu trả lời phải chứa hành động được phép/cấm cùng thời hạn nếu context có nêu.

### #5 — Tạm ứng 15 triệu, hoàn ứng trễ 5 ngày

- **Question:** Nhân viên tạm ứng 15 triệu, sau 20 ngày mới thanh toán. Bị phạt bao nhiêu?
- **Expected:** 2%/tháng trên 15.000.000 VNĐ = 300.000 VNĐ/tháng; quy đổi pro-rata khoảng 50.000 VNĐ cho 5 ngày quá hạn.
- **Observed:** `answer_relevancy = 0.0000`; diagnostic: `Answer doesn't match question`.
- **Error tree:** Context có quy tắc 15 ngày và 2%/tháng? → có trong cùng chính sách → generator có tính phần quá hạn 5 ngày và trả số tiền? → không bảo đảm → lỗi chính là synthesis/calculation.
- **Root cause:** Retriever có thể lấy đúng quy định nhưng prompt không bắt buộc tính toán hay nêu giả định pro-rata, nên câu trả lời có thể dừng ở việc nhắc lại mức phí.
- **Suggested fix:** Bổ sung bước calculator có kiểm soát hoặc mẫu trả lời có trường “dữ kiện / công thức / kết quả”; đánh dấu rõ giả định khi quy đổi theo ngày.

## Error Tree tổng quát

```text
Kết quả chưa đạt kỳ vọng
├── Context thiếu hoặc sai trọng tâm
│   ├── Bảng/section bị tách thành child chunk
│   ├── Hybrid top-k có thêm chunk nhiễu
│   └── Multi-condition không mở rộng từ child về parent
└── Context có căn cứ nhưng câu trả lời chưa đúng trọng tâm
    ├── Bỏ sót phủ định, thời hạn hoặc điều kiện phụ
    ├── Không tổng hợp đủ các evidence liên quan
    └── Không thực hiện phép tính đơn giản theo chính sách
```

## Case study cho presentation

**Câu hỏi:** Laptop 30 triệu cho nhân viên mới cần ai phê duyệt và cần gì từ CNTT?

Đây là một câu multi-condition: cần đồng thời lấy ngưỡng 5–50 triệu (Director), xác nhận cấu hình kỹ thuật của CNTT và quy tắc ít nhất 3 báo giá vì trên 10 triệu. RRF và cross-encoder xếp hạng từng chunk độc lập nên chưa bảo đảm top-3 bao phủ đủ ba evidence. Hướng cải thiện: retrieve top-10 → rerank có diversity/coverage → gộp chunk cùng `source`/section → trả lời theo checklist “người duyệt / yêu cầu CNTT / báo giá”.

## Hạn chế và lần chạy tiếp theo

Report chỉ lưu aggregate và 10 failure, chưa lưu đáp án, context, per-question scores, model, thời điểm chạy và tham số retrieval. Vì vậy phần diagnosis ở trên là phân tích có căn cứ từ metric + corpus, không phải khẳng định về mọi bước trung gian. Lần chạy tiếp theo cần lưu các artefact đó, cố định model/config và chạy lại cùng test set để so sánh tái lập.
