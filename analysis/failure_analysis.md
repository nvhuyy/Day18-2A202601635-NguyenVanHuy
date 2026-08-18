# Failure Analysis — Lab 18: Production RAG

**Nhóm:** Huy01635  
**Thành viên:** Nguyễn Văn Huy — M1, M2, M3, M4  
**Nguồn số liệu:** `naive_baseline_report.json` và `ragas_report.json` (20 câu hỏi)

## Kết quả RAGAS

| Metric | Naive baseline | Production | Δ (Production − Naive) | Nhận xét |
|---|---:|---:|---:|---|
| Faithfulness | 0.5298 | 0.0000* | -0.5298 | `NaN` từ evaluator được chuẩn hóa về giá trị fallback `0.0`; không diễn giải đây là điểm RAGAS hợp lệ. |
| Answer relevancy | 0.0728 | 0.0708 | -0.0020 | Fallback trả đoạn context đầu tiên khi LLM không phản hồi ổn định. |
| Context precision | 0.9292 | 0.8250 | -0.1042 | Contextual prepend làm nhiều chunk có từ vựng chung khi chưa có metadata filter. |
| Context recall | 0.7383 | 0.6708 | -0.0675 | Child chunk ngắn và top-3 sau rerank làm thiếu điều kiện ở câu multi-hop. |

Kết quả hiện tại chưa chứng minh production tốt hơn baseline. Cần sửa retrieval và generation, sau đó chạy lại RAGAS; không điều chỉnh số liệu theo hướng đẹp hơn.

## Bottom-5 failures

### #1 — Mua thiết bị 55 triệu

- **Expected:** CEO phê duyệt vì đơn hàng trên 50.000.000 VNĐ.
- **Observed:** `context_precision = 0.00`.
- **Error tree:** Output chưa đáng tin → context có đúng bảng thẩm quyền? **Không ổn định** → query phân biệt ngưỡng “trên 50 triệu”? **Có** → lỗi chính ở retrieval/ranking.
- **Root cause:** Bảng markdown bị chia thành child chunk; pipeline có thể lấy quy trình/lưu ý CNTT thay vì đúng hàng “trên 50 triệu”.
- **Suggested fix:** Giữ nguyên bảng trong structure-aware chunk, boost thực thể tiền tệ và rerank top-10 trước top-3.

### #2 — Nghỉ không lương 20 ngày

- **Expected:** CEO phê duyệt; nghỉ trên 14 ngày thì tự đóng phần bảo hiểm.
- **Observed:** Faithfulness được lưu là `0.0` theo fallback vì evaluator trả `NaN`; đây không phải phép đo faithfulness hợp lệ.
- **Error tree:** Context đúng chính sách? **Có thể thiếu** → cần ghép “16–30 ngày” và “trên 14 ngày” ở hai section → lỗi multi-condition retrieval.
- **Root cause:** Chỉ đưa child chunk cho LLM, không mở rộng parent/section.
- **Suggested fix:** Trả parent chunk khi child được chọn; prompt yêu cầu liệt kê mọi điều kiện liên quan.

### #3 — Laptop 30 triệu cho nhân viên mới

- **Expected:** Director phê duyệt; cần xác nhận cấu hình CNTT; kèm ít nhất 3 báo giá.
- **Observed:** `context_precision = 0.00`.
- **Error tree:** Context đủ ba điều kiện? **Không chắc** → câu hỏi multi-hop? **Có** → cần tăng recall có kiểm soát.
- **Root cause:** Ba điều kiện nằm ở ba đoạn trong cùng tài liệu, trong khi context cuối chỉ có top-3 chunk.
- **Suggested fix:** Retrieve top-10, gộp chunk cùng `source`/`section`, trả lời theo checklist.

### #4 — Thâm niên được cộng phép

- **Expected:** Từ 3 năm, cộng 1 ngày cho mỗi 3 năm; v2024 thay thế v2023 (5 năm).
- **Observed:** `answer_relevancy = 0.00`.
- **Error tree:** Context đúng version? **Không bảo đảm** → corpus có hai phiên bản? **Có** → lỗi version-aware retrieval.
- **Root cause:** Chưa filter/boost theo `version` và `effective_date`.
- **Suggested fix:** Đưa version, ngày hiệu lực và trạng thái superseded vào metadata; ưu tiên tài liệu mới nhất.

### #5 — Senior 9 năm: phép năm và lương

- **Expected:** 18 ngày phép (15 + 3) và 20–35 triệu VNĐ/tháng.
- **Observed:** `answer_relevancy = 0.00`.
- **Error tree:** Context đủ hai vế? **Chỉ một phần** → cần hai tài liệu → lỗi cross-document multi-hop.
- **Root cause:** Reranker tối ưu từng chunk độc lập, không bảo đảm top-k bao phủ cả phép năm lẫn bảng lương.
- **Suggested fix:** Phân rã thành hai sub-query hoặc coverage-aware reranking.

## Case study cho presentation

**Câu hỏi:** Laptop 30 triệu cho nhân viên mới.

Query có ba ràng buộc: giá trị đơn hàng, thiết bị CNTT, ngưỡng báo giá. RRF/reranker xếp từng chunk nên không bảo đảm lấy đủ ba evidence. Hướng sửa: retrieve top-10 → rerank theo độ liên quan và độ bao phủ → gộp chunk cùng tài liệu → prompt checklist “người duyệt / yêu cầu CNTT / báo giá”.

## Error Tree tổng quát

```text
Kết quả không đạt
├── Context không đủ hoặc sai
│   ├── Chunk tách bảng/section hoặc parent-child
│   ├── Không phân biệt phiên bản chính sách
│   └── Multi-hop thiếu cơ chế coverage
└── Context có nhưng câu trả lời không đúng trọng tâm
    ├── Fallback trả nguyên context khi LLM/API lỗi
    └── Prompt chưa bắt buộc kiểm tra đủ điều kiện và nêu nguồn
```
