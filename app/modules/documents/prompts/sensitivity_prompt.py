IT_SENSITIVITY_PROMPT = """
Bạn đánh giá độ nhạy cảm tài liệu phòng IT. 

0 = PUBLIC
- tài liệu đào tạo
- kiến thức lập trình
- mô tả công việc
- onboarding kỹ thuật

1 = INTERNAL
- API nội bộ
- kiến trúc hệ thống
- deploy
- quy trình vận hành
- tài liệu dự án

2 = PRIVATE
- credential
- token
- cấu hình server
- quyền hệ thống
- thông tin khách hàng

3 = STRICT
- root account
- encryption key
- secret
- chiến lược bảo mật
- backup hệ thống

Chunk:
{content}

Chỉ trả về một số duy nhất trong các số 1, 2, 3, 4 tương ứng với nhưng cái đã nói ở trên.
Chú ý: không giải thích thêm bất kỳ điều gì chỉ trả về một số duy nhất trong các số 1, 2, 3, 4
"""


HR_SENSITIVITY_PROMPT = """
Bạn đánh giá độ nhạy cảm tài liệu phòng HR.

0 = PUBLIC
- nghỉ phép
- onboarding
- quy định chung
- tuyển dụng công khai

1 = INTERNAL
- KPI
- đánh giá năng lực
- quy trình tuyển dụng
- hiệu suất nhân viên

2 = PRIVATE
- bảng lương
- hồ sơ nhân sự
- thưởng phạt
- hợp đồng lao động

3 = STRICT
- sa thải
- kỷ luật
- tranh chấp lao động
- điều tra nội bộ

Chunk:
{content}

Chỉ trả về một số duy nhất trong các số 1, 2, 3, 4 tương ứng với nhưng cái đã nói ở trên.
Chú ý: không giải thích thêm bất kỳ điều gì chỉ trả về một số duy nhất trong các số 1, 2, 3, 4
"""


SALES_SENSITIVITY_PROMPT = """
Bạn đánh giá độ nhạy cảm tài liệu Sales.

0 = PUBLIC
- giới thiệu sản phẩm
- tài liệu bán hàng
- quy trình chung

1 = INTERNAL
- KPI sales
- pipeline
- chiến dịch bán hàng

2 = PRIVATE
- doanh số từng người
- khách hàng lớn
- hợp đồng đang đàm phán

3 = STRICT
- chiến lược giá
- danh sách khách hàng VIP
- dữ liệu doanh thu chiến lược

Chunk:
{content}

Chỉ trả về một số duy nhất trong các số 1, 2, 3, 4 tương ứng với nhưng cái đã nói ở trên.
Chú ý: không giải thích thêm bất kỳ điều gì chỉ trả về một số duy nhất trong các số 1, 2, 3, 4
"""


MARKETING_SENSITIVITY_PROMPT = """
Bạn đánh giá độ nhạy cảm tài liệu Marketing.

0 = PUBLIC
- nội dung quảng bá
- bài viết công khai
- giới thiệu thương hiệu

1 = INTERNAL
- kế hoạch chiến dịch
- KPI marketing
- lịch nội dung

2 = PRIVATE
- ngân sách marketing
- phân tích đối thủ
- hiệu quả quảng cáo

3 = STRICT
- chiến lược thương hiệu dài hạn
- dữ liệu khách hàng
- kế hoạch chưa công bố

Chunk:
{content}

Chỉ trả về một số duy nhất trong các số 1, 2, 3, 4 tương ứng với nhưng cái đã nói ở trên.
Chú ý: không giải thích thêm bất kỳ điều gì chỉ trả về một số duy nhất trong các số 1, 2, 3, 4
"""



