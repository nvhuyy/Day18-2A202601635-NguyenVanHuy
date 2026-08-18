# Group Report — Lab 18: Production RAG

**Nhóm:** Huy01635  
**Ngày:** 18/08/2026

## Thành viên & phạm vi thực hiện

| Thành viên | Module/phạm vi | Trạng thái |
|---|---|---|
| Nguyễn Văn Huy — 2A202601635 | M1 Chunking, M2 Hybrid Search, M3 Reranking, M4 Evaluation; tích hợp M5 | Đã triển khai và tạo report 20 câu hỏi |

## Kết quả RAGAS

| Metric | Naive | Production | Δ |
|---|---:|---:|---:|
| Faithfulness | 0.5817 | 0.7072 | +0.1256 |
| Answer relevancy | 0.0811 | 0.0798 | -0.0013 |
| Context precision | 0.8792 | 0.7583 | -0.1208 |
| Context recall | 0.7333 | 0.7375 | +0.0042 |

Production đạt ngưỡng 0.70 ở 3 metric: faithfulness, context precision và context recall. Faithfulness tăng rõ rệt, còn context recall tăng nhẹ. Đổi lại, hybrid retrieval làm context precision giảm, và answer relevancy là điểm yếu lớn nhất ở cả baseline lẫn production.

## Key findings

1. Reranking + context có vẻ giúp câu trả lời bám evidence hơn, thể hiện ở faithfulness tăng 0.1256.
2. Các câu có bảng, ngưỡng tiền, điều kiện phủ định hoặc nhiều bước suy luận vẫn dễ thất bại do top-k thiếu coverage hoặc câu trả lời không tổng hợp đúng trọng tâm.
3. Corpus có các chính sách cũ/mới (phép năm, mật khẩu); metadata hiện có chưa tách rõ `version`, `effective_date` và trạng thái thay thế để retrieval ưu tiên bản hiện hành.
4. Report hiện chưa lưu per-question answers/contexts và cấu hình chạy, nên chưa đủ để audit hoặc tái lập chi tiết từng failure.

## Kế hoạch cải thiện có thể đo lường

1. Bảo toàn cấu trúc bảng/section; retrieve child nhưng đưa parent section liên quan vào context cuối.
2. Bổ sung metadata `source`, `section`, `version`, `effective_date`, `status`; boost phiên bản hiện hành khi query không chỉ rõ năm.
3. Retrieve top-10 và chọn context theo coverage theo tài liệu/điều kiện, thay vì chỉ lấy top-3 score cao nhất.
4. Chuẩn hóa prompt trả lời theo “kết luận → căn cứ → phép tính/điều kiện”; thêm kiểm tra negation và phép tính policy.
5. Lưu per-question answer, contexts, 4 scores, model/config và timestamp; chạy lại đúng 20 câu để đo trước–sau.
