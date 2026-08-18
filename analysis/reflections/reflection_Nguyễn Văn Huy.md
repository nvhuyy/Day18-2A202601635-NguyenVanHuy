# Individual Reflection — Lab 18

**Tên:** Nguyễn Văn Huy — 2A202601635  
**Module phụ trách:** M1, M2, M3, M4; tích hợp M5

## 1. Mapping bài giảng vào code

| Lecture concept | Module | Hàm/class cụ thể | Quan sát từ bài lab |
|---|---|---|---|
| Semantic, hierarchical và structure-aware chunking | M1 | `chunk_semantic()`, `chunk_hierarchical()`, `chunk_structure_aware()` | Hierarchical phù hợp truy hồi đoạn nhỏ; structure-aware cần giữ trọn bảng/ngưỡng chính sách. |
| BM25 + dense fusion | M2 | `segment_vietnamese()`, `BM25Search`, `reciprocal_rank_fusion()` | BM25 cần tách từ tiếng Việt nhất quán; RRF không tự bảo đảm đủ evidence cho multi-hop. |
| Cross-encoder reranking | M3 | `CrossEncoderReranker.rerank()` | Rerank lọc candidate tốt nhưng có thể chọn các chunk cùng một ý và bỏ ý thứ hai. |
| Đánh giá RAGAS | M4 | `evaluate_ragas()`, `failure_analysis()` | Bốn metric tách lỗi retrieval/generation; `NaN` được chuẩn hóa thành fallback `0.0`, không phải một score RAGAS hợp lệ. |
| Contextual embeddings/enrichment | M5 | `_enrich_single_call()`, `contextual_prepend()` | Thêm ngữ cảnh nguồn giúp truy hồi chủ đề, nhưng thiếu metadata filter sẽ làm precision giảm. |

## 2. Đóng góp kỹ thuật

- Hoàn thiện luồng chunking, hybrid retrieval, reranking, RAGAS và nối enrichment vào pipeline.
- Dùng `failure_analysis()` để xếp Bottom-N theo metric yếu nhất, gắn diagnosis và suggested fix.
- Kiểm tra corpus có chính sách cũ/mới; đưa version-aware retrieval và multi-hop coverage thành đề xuất cải tiến trọng tâm.

## 3. Khó khăn & cách giải quyết

- **Lỗi thực tế:** `ModuleNotFoundError: No module named 'pypdf'` khi `load_documents()` đọc `data/BCTC.pdf`; `ModuleNotFoundError: No module named 'underthesea'` và `No module named 'rank_bm25'` ở M2.
- **Cách debug:** chạy test theo module để tách lỗi code với dependency, đọc traceback đến import lỗi và đối chiếu `requirements.txt`.
- **Vấn đề đánh giá:** production report có `NaN` cho faithfulness. Mình chuẩn hóa thành fallback `0.0` trong JSON để report hợp lệ, đồng thời ghi rõ đây không phải score RAGAS hợp lệ.
- **Kiến thức cần bổ sung:** retrieval cho bảng markdown, tài liệu có version và câu hỏi cần nhiều evidence thay vì chỉ tối ưu similarity từng chunk.

## 4. Nếu làm lại

- Cài dependency vào đúng virtual environment và smoke test trước benchmark.
- Lưu `source`, `section`, `version`, `effective_date`; khi chọn child sẽ mở rộng context về parent section.
- Tách câu multi-hop thành sub-query hoặc coverage-aware reranking; yêu cầu LLM trả lời theo điều kiện và nêu nguồn.

## 5. Action plan cho project cá nhân

### Project: Trợ lý tra cứu chính sách nội bộ

**Hiện tại:** Pipeline có chunking, hybrid search, reranking, enrichment và RAGAS. Điểm yếu là fallback có thể trả nguyên context; retrieval chưa ưu tiên version hiện hành và chưa bao phủ tốt multi-hop.

1. [ ] **Chunking:** structure-aware cho chính sách/bảng; child khoảng 256 tokens, parent/section làm context cuối.
2. [ ] **Search:** BM25 + dense + RRF, filter theo nguồn/phiên bản khi query không nêu năm.
3. [ ] **Reranking:** rerank top-10 rồi chọn evidence có coverage nhiều chủ đề; benchmark latency trước khi tăng top-k.
4. [ ] **Evaluation:** RAGAS 4 metrics trên test set có version, negation và multi-hop; chỉ lưu score hữu hạn kèm model/config.
5. [ ] **Enrichment:** bắt đầu contextual prepend + metadata; chỉ bật combined LLM enrichment sau khi đo precision/recall trước–sau.

### Timeline

- **Tuần 1:** khóa dependency, chạy xanh toàn bộ test, thêm metadata version/section và regression test cho chính sách cũ–mới.
- **Tuần 2:** triển khai parent expansion và coverage-aware rerank; kiểm tra 5 failure case.
- **Tuần 3:** chạy lại RAGAS bằng model ổn định, so sánh baseline và cập nhật failure analysis theo số liệu mới.

## 6. Tự đánh giá

| Tiêu chí | Tự chấm (1–5) | Cơ sở |
|---|---:|---|
| Hiểu bài giảng | 4 | Phân biệt được lỗi chunking, retrieval, rerank và generation qua Error Tree. |
| Code quality | 3 | Luồng module rõ nhưng cần harden dependency/fallback và xử lý giá trị không hữu hạn. |
| Teamwork | 4 | Phạm vi và phát hiện được ghi rõ để người khác tái lập. |
| Problem solving | 4 | Dùng traceback, corpus và metric để đi từ triệu chứng đến nguyên nhân kiểm chứng được. |
