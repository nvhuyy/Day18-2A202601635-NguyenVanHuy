# Group Report — Lab 18: Production RAG

**Nhóm:** Huy01635  
**Ngày:** 18/08/2026

## Thành viên & phạm vi thực hiện

| Thành viên | Module | Trạng thái | Kiểm tra đã thực hiện |
|---|---|---|---|
| Nguyễn Văn Huy — 2A202601635 | M1 Chunking, M2 Hybrid Search, M3 Reranking, M4 Evaluation; tích hợp M5 | Đã triển khai | Các test unit không cần dependency/model ngoài đã pass; các test M1/M2 còn lại bị chặn bởi package thiếu trong môi trường hiện tại. |

Lỗi môi trường đã xác nhận: `ModuleNotFoundError: No module named 'pypdf'`, `underthesea` và `rank_bm25`. Đây là dependency runtime, không phải kết quả đánh giá retrieval.

## Kết quả RAGAS

| Metric | Naive | Production | Δ |
|---|---:|---:|---:|
| Faithfulness | 0.5298 | 0.0000* | -0.5298 |
| Answer relevancy | 0.0728 | 0.0708 | -0.0020 |
| Context precision | 0.9292 | 0.8250 | -0.1042 |
| Context recall | 0.7383 | 0.6708 | -0.0675 |

`NaN` đã được chuẩn hóa thành giá trị fallback `0.0` trong JSON để báo cáo hợp lệ và có thể hiển thị. Dấu `*` nghĩa là evaluator không trả metric hợp lệ, không phải faithfulness thực nghiệm. Chưa có cơ sở để tuyên bố production cải thiện baseline; cần cài đủ dependency, dùng một cấu hình LLM nhất quán rồi chạy lại 20 câu.

## Key findings

1. Pipeline đã ghép M1 → M5 → M2 → M3 → M4, nhưng quality end-to-end đang bị chi phối bởi fallback generation.
2. Câu multi-hop cần nhiều điều kiện/nhiều tài liệu là điểm yếu lớn nhất; rerank từng chunk không đảm bảo evidence coverage.
3. Contextual enrichment có thể giảm vocabulary gap, nhưng khi chưa lọc metadata/version lại làm precision giảm vì nhiều chunk có tiền tố tương tự.

## Kế hoạch cải thiện có thể đo lường

1. Cài và khóa dependency trong `requirements.txt`, chạy test bằng đúng `.venv` của dự án.
2. Giữ header/bảng trong structure-aware chunk; retrieve child nhưng đưa parent/section vào context cuối.
3. Thêm metadata `version`, `effective_date`, `source`, `section`; ưu tiên chính sách hiện hành.
4. Retrieve top-10, coverage-aware rerank rồi gộp evidence theo tài liệu cho câu multi-hop.
5. Chỉ công bố RAGAS khi 4 metric đều hữu hạn; lưu model/config và thời điểm chạy để tái lập.
