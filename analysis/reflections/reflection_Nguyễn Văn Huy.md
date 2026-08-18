# Individual Reflection — Lab 18

**Tên:** Nguyễn Văn Huy — 2A202601635  
**Module phụ trách:** M1, M2, M3, M4; tích hợp M5

## 1. Mapping bài giảng vào code

| Lecture concept | Module | Hàm/class cụ thể | Quan sát từ lab |
|---|---|---|---|
| Semantic, hierarchical, structure-aware chunking | M1 | `chunk_semantic()`, `chunk_hierarchical()`, `chunk_structure_aware()` | Child chunk phù hợp cho truy hồi chính xác, nhưng các bảng và quy tắc nhiều điều kiện cần giữ section/parent để không mất ngữ cảnh. |
| BM25 + dense fusion | M2 | `segment_vietnamese()`, `BM25Search`, `DenseSearch`, `reciprocal_rank_fusion()` | RRF tăng cơ hội lấy evidence khác cách diễn đạt, nhưng production context precision giảm 0.1208 so với baseline: fusion không tự loại được chunk nhiễu. |
| Cross-encoder reranking | M3 | `CrossEncoderReranker.rerank()` | Reranker giúp chọn chunk phù hợp hơn từng câu hỏi, nhưng xếp hạng độc lập chưa bảo đảm coverage cho câu multi-hop. |
| Đánh giá RAGAS | M4 | `evaluate_ragas()`, `failure_analysis()` | Report 20 câu cho thấy 3/4 metric production ≥ 0.70; answer relevancy 0.0798 là metric thấp nhất và cần ưu tiên sửa ở generation/synthesis. |
| Contextual enrichment | M5 | `_enrich_single_call()`, `contextual_prepend()` | Contextual prepend có thể thu hẹp vocabulary gap; cần kết hợp metadata version/section để không làm top-k lẫn các chunk tương tự. |

## 2. Đóng góp kỹ thuật

- Hoàn thiện luồng chunking, hybrid retrieval, reranking và RAGAS; nối enrichment vào pipeline trước bước index.
- Dùng `failure_analysis()` để sắp xếp các câu có điểm trung bình thấp và ánh xạ metric yếu nhất sang diagnosis/suggested fix.
- Đối chiếu failure với corpus để nhận diện ba nhóm khó: bảng/ngưỡng số tiền, câu phủ định/điều kiện và câu cần tổng hợp hoặc tính toán.
- Rà soát report hiện có: production tăng faithfulness từ 0.5817 lên 0.7072 và context recall từ 0.7333 lên 0.7375, nhưng answer relevancy chưa cải thiện.

## 3. Khó khăn & cách giải quyết

- **Vấn đề môi trường quan sát được:** chạy bằng Python hệ thống báo `No module named pytest`; `check_lab.py` lỗi `UnicodeEncodeError: 'charmap' codec can't encode character '\\U0001f50d'` trên console Windows dùng cp1252. Khi chuyển sang `.venv`, pytest bắt đầu chạy nhưng test semantic phải nạp model `all-MiniLM-L6-v2` nên vượt thời gian kiểm tra 120 giây.
- **Cách debug:** tách lỗi theo interpreter và theo module, dùng `.venv\\Scripts\\python.exe`, đặt `PYTHONIOENCODING=utf-8` khi chạy console, rồi xác định điểm chậm tại model loading thay vì gán nhầm cho logic test.
- **Vấn đề đánh giá:** JSON hiện chỉ có aggregate và failure summary nên không thể xác nhận chính xác context/answer của từng case. Mình đối chiếu metric với ground truth và tài liệu nguồn, đồng thời ghi rõ đây là suy luận chẩn đoán.
- **Kiến thức cần bổ sung:** version-aware retrieval, xử lý bảng Markdown, coverage-aware reranking, và generation có cấu trúc cho phủ định hoặc phép tính.

## 4. Nếu làm lại

- Cache/pre-download các embedding và reranker model, sau đó chạy smoke test theo đúng `.venv` trước benchmark.
- Lưu `source`, `section`, `version`, `effective_date`, `status`; khi chọn child sẽ mở rộng sang parent/section.
- Tách câu multi-hop thành sub-query hoặc dùng diversity/coverage reranking; prompt yêu cầu trả lời theo checklist và nêu căn cứ.
- Lưu đáp án, context, per-question scores và cấu hình chạy trong report để failure analysis có thể tái lập.

## 5. Action plan cho project cá nhân

### Project: Trợ lý tra cứu chính sách nội bộ

**Hiện tại:** Pipeline gồm chunking, hybrid search, reranking, enrichment và RAGAS. Điểm mạnh là faithfulness cải thiện; điểm yếu là answer synthesis, version-aware retrieval và coverage cho câu nhiều điều kiện.

1. [ ] **Chunking:** Dùng structure-aware cho chính sách/bảng; child khoảng 256 tokens, parent/section là context mở rộng.
2. [ ] **Search:** BM25 + dense + RRF; filter/boost phiên bản hiện hành khi query không nêu năm.
3. [ ] **Reranking:** Rerank top-10, sau đó chọn evidence đa dạng theo document/section thay vì chỉ top-3.
4. [ ] **Evaluation:** Chạy RAGAS 4 metric trên test set có version, negation, multi-hop và numeric; lưu đủ per-question artefact.
5. [ ] **Enrichment:** Bắt đầu contextual prepend + metadata; benchmark precision/recall trước–sau combined enrichment.

### Timeline

- **Tuần 1:** Khóa interpreter/dependency, cache model, thêm metadata version/section/status và regression test cho chính sách cũ–mới.
- **Tuần 2:** Triển khai parent expansion, coverage-aware rerank và prompt checklist; kiểm tra 5 failure case hiện tại.
- **Tuần 3:** Chạy lại benchmark 20 câu với cấu hình cố định, so sánh baseline/production và cập nhật failure analysis từ per-question evidence.

## 6. Tự đánh giá

| Tiêu chí | Tự chấm (1–5) | Cơ sở |
|---|---:|---|
| Hiểu bài giảng | 4 | Phân biệt được lỗi ở chunking, retrieval, rerank và generation qua metric/error tree. |
| Code quality | 3 | Module tách rõ; vẫn cần cache model, lưu artefact evaluation và làm cứng fallback. |
| Teamwork | 4 | Phạm vi, số liệu nguồn và giới hạn đánh giá được ghi rõ để người khác tái lập. |
| Problem solving | 4 | Dùng traceback, test environment, metric và corpus để đi từ triệu chứng đến giả thuyết có thể kiểm tra. |
