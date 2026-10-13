import json

from backend.app.shared.llm.llm_factory import (
    LLMFactory
)
from backend.app.shared.json_helper import (
    JsonHelper
)
from backend.app.shared.llm.llm_failover_service import (LLMFailoverService)

class EntityExtractor:

    

    async def extract(
        self,
        content: str
    ) -> dict:

        prompt = f"""
Phân tích đoạn văn dưới đây.

Trích xuất:

1. Các entity quan trọng.

Với mỗi entity trả về:

- name
- type
- description

Trong đó:

name:
Tên entity.

type:
Một trong các giá trị:

- Person
- Department
- System
- Technology
- Process
- Document
- Policy
- Other

description:
Mô tả ngắn gọn vai trò, chức năng hoặc ý nghĩa
của entity trong chính đoạn văn này.

--------------------------------------------------

2. Các mối quan hệ giữa các entity
TRONG CHÍNH ĐOẠN VĂN NÀY.

Với mỗi relationship trả về:

- source
- target
- description

Trong đó:

source:
Entity nguồn.

target:
Entity đích.

description:
Mô tả ngắn gọn mối quan hệ giữa hai entity.

Chỉ tạo relationship nếu mối quan hệ
được thể hiện rõ trong đoạn văn.

--------------------------------------------------

Chỉ trả về JSON hợp lệ.

dưới đây là mẫu JSON bạn hãy dựa theo:

{{
  "entities": [
    {{
      "name": "Redis",
      "type": "Technology",
      "description": "Lưu thông tin phiên làm việc."
    }},
    {{
      "name": "Authentication",
      "type": "System",
      "description": "Sử dụng dữ liệu phiên làm việc để xác thực người dùng."
    }}
  ],

  "relationships": [
    {{
      "source": "Authentication",
      "target": "Redis",
      "description": "Authentication sử dụng dữ liệu phiên làm việc được lưu trong Redis."
    }}
  ]
}}

ĐOẠN VĂN:

{content}
"""

        response = await (

            LLMFailoverService
            .generate(
                prompt
            )

        )
        
        print(
        "\n========== RAW RESPONSE ==========\n"
        )

        #print(response)

        print(
            "\n==================================\n"
        )

        try:

            parsed = (
            JsonHelper
            .parse_llm_json(
                response
            )
        )  
            print("in ra response sau parse", parsed)

            return {

                "entities":
                parsed.get(
                    "entities",
                    []
                ),

                "relationships":
                parsed.get(
                    "relationships",
                    []
                )
            }

        except Exception as e:

            print(
                "[EntityExtractor]",
                e
            )

            return {

                "entities": [],

                "relationships": []
            }