
# 소비 스키마 -> 아래의 경우는 잘못된 거 같음.
PUT /consuming_index_prod_nori
{
  "settings": {
    "index": {
      "analysis": {
        "tokenizer": {
          "nori_user_dict": {
            "type": "nori_tokenizer",
            "decompound_mode": "mixed",
            "user_dictionary_rules": [
              "숙박",
              "오프라인쇼핑",
              "병원",
              "카페",
              "인터넷쇼핑",
              "구독서비스",
              "식사",
              "미용",
              "게임",
              "친목",
              "건강",
              "학습",
              "야놀자"

            ]
          }
        },
        "filter": {
          "my_synonyms": {
            "type": "synonym_graph",
            "synonyms": [
              "야놀자, 여기어때 => 숙박",
              "매점, 마트, 할인점, 스타필드, 세븐일레븐, 이마트, 더 현대, gs25, cu, 우정버스, 백화점, 편의점, 몰, 문고, 씨유, 롯데 프리미엄, 가락시장, 세븐 일레븐, 롯데물산 => 오프라인쇼핑",
              "내과, 약국, 의원, 의학, 정신과, 치과 => 병원",
              "스타벅스, 커피, 뚜레쥬르, 제빵, 나폴레옹, 파리바게트, 로흐, 폴바셋, 공차, 빵집, 스트로베리32, 구슬아이스크림, 보드게임, 베이커리, 베스킨라빈스, 센소, 도넛, 나인블럭, 뚜레주르, 이성당 => 카페",
              "네이버, 위메프, 쿠팡, 카카오, 큐텐, 올리브영, 옥션 => 인터넷 쇼핑",
              "멜론, 넷플릭스, 유튜브, chatgpt, sk, 통신비, 웹하드, 정수기 => 구독 서비스",
              "꽃게, 한우천국, 우아한 형제들, 옥된장, 아웃백, 담미온, 설렁탕, 청년다방, 순대, 효동각, 돈까스, 초밥, 곱창, 오근내, 치킨, 통닭, 버거, 까폼, 아지사이, 아구찜, 마라탕, 스시, 딘타이펑, 파이브가이즈, 서브웨이, 스테이크, 닭도리탕, 삼겹살, 취원, 비비큐, 닭갈비, 피슈마라홍, 떡볶이, 족발, 분식, 찜닭, L&M, 샤브샤브, 슈하스코, 강남면옥, 고우, 갈비, 매드포갈릭, 김치찌개, 조개구이, 회, 헬로브라질, 후타리, 짬뽕, 텍사스데 브라질, 아그라, 피자, 식당  => 식사",
              "위캔두잇, 헤어 => 미용",
              "steam, 스팀게임, 스팀  => 게임",
              "모임, 회식  => 친목",
              "헬스  => 건강",
              "인프런  => 학슴"
            ]
          },
          "nori_pos_filter": {
            "type": "nori_part_of_speech",
            "stoptags": ["E", "IC", "J", "MAG", "MM", "NA", "NR", "SC", "SE", "SF", "SH", "SL", "SN", "SP", "SSC", "SSO", "SY", "UNA", "UNKNOWN", "VA", "VCN", "VCP", "VV", "VX", "XPN", "XR", "XSA", "XSN", "XSV"]
          }
        },
        "analyzer": {
          "custom_nori_analyzer": {
            "type": "custom",
            "tokenizer": "nori_user_dict",
            "filter": [
              "nori_pos_filter",
              "lowercase",
              "my_synonyms"
            ]
          }
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "@timestamp": {
        "type": "date"
      },
      "prodt_name": {
        "type": "text",
        "analyzer": "custom_nori_analyzer"
      },
      "prodt_money": {
        "type": "long"
      }
    }
  }
}