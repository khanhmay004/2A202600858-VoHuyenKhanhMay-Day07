# Benchmark — Cellphones Policy Retrieval

- Embedder: `paraphrase-multilingual-MiniLM-L12-v2`
- Docs: 6  |  Queries: 5  |  top_k: 3

## Strategy `fixed_size_300`

- Total chunks: **123**  |  avg chunk length: **294** chars  |  index time: 4.8s

| # | Query | Mode | Top-1 doc | Top-1 score | Top-3 docs | Hit@3 | Top-1 chunk |
|---|-------|------|-----------|------------:|------------|:-----:|-------------|
| 1 | Cellphones.com.vn do công ty nào sở hữu và quy định chu | search | `tos` | 0.778 | tos/tos/tos | Y | hoạt động và vận hành với tên miền giao dịch là www.cellphones.com.vn (sau đây gọi là Webs… |
| 1 | Cellphones.com.vn do công ty nào sở hữu và quy định chu | filter | `tos` | 0.778 | tos/tos/tos | Y | hoạt động và vận hành với tên miền giao dịch là www.cellphones.com.vn (sau đây gọi là Webs… |
| 2 | Phí giao hàng nội thành Hà Nội như thế nào? | search | `chinh_sach_giao_hang` | 0.773 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | Y | Store Thanh Hóa. Khi thanh toán online tôi không thể chọn giao về Hà Nội được. Hơn nữa, tr… |
| 2 | Phí giao hàng nội thành Hà Nội như thế nào? | filter | `chinh_sach_giao_hang` | 0.773 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | Y | Store Thanh Hóa. Khi thanh toán online tôi không thể chọn giao về Hà Nội được. Hơn nữa, tr… |
| 3 | Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành  | search | `chinh_sach_khui_hop_apple` | 0.584 | chinh_sach_khui_hop_apple/quy_dinh_sao_luu_du_lieu/chinh_sach_khui_hop_apple | Y | àng tại địa điểm ngoài Cửa hàng để đảm bảo quyền lợi của khách hàng. - Khách hàng phải tha… |
| 3 | Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành  | filter | `chinh_sach_khui_hop_apple` | 0.584 | chinh_sach_khui_hop_apple/chinh_sach_khui_hop_apple/chinh_sach_khui_hop_apple | Y | àng tại địa điểm ngoài Cửa hàng để đảm bảo quyền lợi của khách hàng. - Khách hàng phải tha… |
| 4 | Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 | search | `chinh_sach_giao_hang` | 0.675 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | n | ông ty và chữ ký người đại diện Pháp luật công ty. Trường hợp Quý khách không cung cấp đầy… |
| 4 | Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 | filter | `bieu_phi_bao_hanh_mo_rong` | 0.579 | bieu_phi_bao_hanh_mo_rong/bieu_phi_bao_hanh_mo_rong/bieu_phi_bao_hanh_mo_rong | Y | ện cao cấp, Macbook, điện thoại mới. * Thời gian tham gia: 24 tháng đến 36 tháng bao gồm 1… |
| 5 | Mua trả góp qua thẻ tín dụng tại Cellphones cần điều ki | search | `huong_dan_mua_tra_gop` | 0.808 | huong_dan_mua_tra_gop/chinh_sach_giao_hang/huong_dan_mua_tra_gop | Y | à điền mẫu đơn đăng ký chuyển đổi trả góp tại CellphoneS, CellphoneS sẽ gửi ngân hàng và t… |
| 5 | Mua trả góp qua thẻ tín dụng tại Cellphones cần điều ki | filter | `huong_dan_mua_tra_gop` | 0.808 | huong_dan_mua_tra_gop/huong_dan_mua_tra_gop/huong_dan_mua_tra_gop | Y | à điền mẫu đơn đăng ký chuyển đổi trả góp tại CellphoneS, CellphoneS sẽ gửi ngân hàng và t… |

**Hit@3 (search)** = 4/5    **Hit@3 (filter)** = 5/5

## Strategy `by_sentences_3`

- Total chunks: **67**  |  avg chunk length: **485** chars  |  index time: 2.2s

| # | Query | Mode | Top-1 doc | Top-1 score | Top-3 docs | Hit@3 | Top-1 chunk |
|---|-------|------|-----------|------------:|------------|:-----:|-------------|
| 1 | Cellphones.com.vn do công ty nào sở hữu và quy định chu | search | `tos` | 0.794 | tos/tos/bieu_phi_bao_hanh_mo_rong | Y | <!-- category: tos --> # Quy chế hoạt động website Cellphones.com.vn PHẦN I. QUY ĐỊNH CHUN… |
| 1 | Cellphones.com.vn do công ty nào sở hữu và quy định chu | filter | `tos` | 0.794 | tos/tos/tos | Y | <!-- category: tos --> # Quy chế hoạt động website Cellphones.com.vn PHẦN I. QUY ĐỊNH CHUN… |
| 2 | Phí giao hàng nội thành Hà Nội như thế nào? | search | `chinh_sach_giao_hang` | 0.649 | chinh_sach_giao_hang/chinh_sach_giao_hang/tos | Y | Tuy nhiên Sản phẩm Ipad Pro M4 lại chỉ còn tại Store Thanh Hóa. Khi thanh toán online tôi … |
| 2 | Phí giao hàng nội thành Hà Nội như thế nào? | filter | `chinh_sach_giao_hang` | 0.649 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | Y | Tuy nhiên Sản phẩm Ipad Pro M4 lại chỉ còn tại Store Thanh Hóa. Khi thanh toán online tôi … |
| 3 | Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành  | search | `quy_dinh_sao_luu_du_lieu` | 0.668 | quy_dinh_sao_luu_du_lieu/chinh_sach_khui_hop_apple/chinh_sach_khui_hop_apple | Y | iPhone** Khách hàng tự sao lưu bằng các hình thức sau: Sao lưu dữ liệu lên iCloud, tạo bản… |
| 3 | Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành  | filter | `chinh_sach_khui_hop_apple` | 0.582 | chinh_sach_khui_hop_apple/chinh_sach_khui_hop_apple/chinh_sach_khui_hop_apple | Y | - **Mở hộp khui seal để kiểm tra thẩm mỹ (không kích hoạt (active) iPhone):** + Trong quá … |
| 4 | Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 | search | `chinh_sach_giao_hang` | 0.691 | chinh_sach_giao_hang/chinh_sach_giao_hang/bieu_phi_bao_hanh_mo_rong | Y | Trường hợp Quý khách không cung cấp đầy đủ chứng từ trên, CellphoneS xin phép thu 8% hoặc … |
| 4 | Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 | filter | `bieu_phi_bao_hanh_mo_rong` | 0.628 | bieu_phi_bao_hanh_mo_rong/bieu_phi_bao_hanh_mo_rong/bieu_phi_bao_hanh_mo_rong | Y | * Quyền lợi và dịch vụ bảo hành: + Tặng gói Bảo hành 1 đổi 1 VIP ( xem chi tiết gói 1 đổi … |
| 5 | Mua trả góp qua thẻ tín dụng tại Cellphones cần điều ki | search | `chinh_sach_giao_hang` | 0.800 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | n | Các quy định khi giao nhận hàng: - Với các đơn hàng từ 10 triệu đồng trở lên, CellphoneS x… |
| 5 | Mua trả góp qua thẻ tín dụng tại Cellphones cần điều ki | filter | `huong_dan_mua_tra_gop` | 0.586 | huong_dan_mua_tra_gop/huong_dan_mua_tra_gop/huong_dan_mua_tra_gop | Y | - Chương trình ưu đãi chỉ áp dụng cho khách hàng lẻ, CellphoneS bảo lưu quyền từ chối áp d… |

**Hit@3 (search)** = 4/5    **Hit@3 (filter)** = 5/5

## Strategy `recursive_300`

- Total chunks: **154**  |  avg chunk length: **210** chars  |  index time: 4.5s

| # | Query | Mode | Top-1 doc | Top-1 score | Top-3 docs | Hit@3 | Top-1 chunk |
|---|-------|------|-----------|------------:|------------|:-----:|-------------|
| 1 | Cellphones.com.vn do công ty nào sở hữu và quy định chu | search | `tos` | 0.840 | tos/tos/chinh_sach_giao_hang | Y | - Website thương mại điện tử Cellphones.com.vn là sở hữu của Công ty TNHH Thương mại và Dị… |
| 1 | Cellphones.com.vn do công ty nào sở hữu và quy định chu | filter | `tos` | 0.840 | tos/tos/tos | Y | - Website thương mại điện tử Cellphones.com.vn là sở hữu của Công ty TNHH Thương mại và Dị… |
| 2 | Phí giao hàng nội thành Hà Nội như thế nào? | search | `chinh_sach_giao_hang` | 0.678 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | Y | - Thời gian giao hàng trong ngày nội thành khu vực Hồ Chí Minh và Hà Nội từ: 8:00 - 20:00.… |
| 2 | Phí giao hàng nội thành Hà Nội như thế nào? | filter | `chinh_sach_giao_hang` | 0.678 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | Y | - Thời gian giao hàng trong ngày nội thành khu vực Hồ Chí Minh và Hà Nội từ: 8:00 - 20:00.… |
| 3 | Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành  | search | `chinh_sach_khui_hop_apple` | 0.621 | chinh_sach_khui_hop_apple/huong_dan_mua_tra_gop/huong_dan_mua_tra_gop | Y | - **Mở hộp khui seal để kiểm tra thẩm mỹ (không kích hoạt (active) iPhone):** |
| 3 | Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành  | filter | `chinh_sach_khui_hop_apple` | 0.621 | chinh_sach_khui_hop_apple/chinh_sach_khui_hop_apple/chinh_sach_khui_hop_apple | Y | - **Mở hộp khui seal để kiểm tra thẩm mỹ (không kích hoạt (active) iPhone):** |
| 4 | Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 | search | `chinh_sach_giao_hang` | 0.635 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | n | Trường hợp Quý khách không cung cấp đầy đủ chứng từ trên, CellphoneS xin phép thu 8% hoặc … |
| 4 | Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 | filter | `bieu_phi_bao_hanh_mo_rong` | 0.568 | bieu_phi_bao_hanh_mo_rong/bieu_phi_bao_hanh_mo_rong/bieu_phi_bao_hanh_mo_rong | Y | Ngoài ra, nhằm mang đến sự an tâm và tiện lợi hơn cho Quý khách hàng trong quá trình sử dụ… |
| 5 | Mua trả góp qua thẻ tín dụng tại Cellphones cần điều ki | search | `chinh_sach_giao_hang` | 0.779 | chinh_sach_giao_hang/huong_dan_mua_tra_gop/huong_dan_mua_tra_gop | Y | - Với các đơn hàng từ 10 triệu đồng trở lên, CellphoneS xin phép kiểm tra thẻ thanh toán v… |
| 5 | Mua trả góp qua thẻ tín dụng tại Cellphones cần điều ki | filter | `huong_dan_mua_tra_gop` | 0.779 | huong_dan_mua_tra_gop/huong_dan_mua_tra_gop/huong_dan_mua_tra_gop | Y | - Ngân hàng liên kết trực tiếp CellphoneS: khách hàng tiến hành cà thẻ và điền mẫu đơn đăn… |

**Hit@3 (search)** = 4/5    **Hit@3 (filter)** = 5/5

## Strategy `structure_aware_600`

- Total chunks: **60**  |  avg chunk length: **542** chars  |  index time: 2.4s

| # | Query | Mode | Top-1 doc | Top-1 score | Top-3 docs | Hit@3 | Top-1 chunk |
|---|-------|------|-----------|------------:|------------|:-----:|-------------|
| 1 | Cellphones.com.vn do công ty nào sở hữu và quy định chu | search | `tos` | 0.842 | tos/chinh_sach_giao_hang/quy_dinh_sao_luu_du_lieu | Y | - Website thương mại điện tử Cellphones.com.vn là sở hữu của Công ty TNHH Thương mại và Dị… |
| 1 | Cellphones.com.vn do công ty nào sở hữu và quy định chu | filter | `tos` | 0.842 | tos/tos/tos | Y | - Website thương mại điện tử Cellphones.com.vn là sở hữu của Công ty TNHH Thương mại và Dị… |
| 2 | Phí giao hàng nội thành Hà Nội như thế nào? | search | `chinh_sach_giao_hang` | 0.627 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | Y | Tôi ở Hà Nội. Tuy nhiên Sản phẩm Ipad Pro M4 lại chỉ còn tại Store Thanh Hóa. Khi thanh to… |
| 2 | Phí giao hàng nội thành Hà Nội như thế nào? | filter | `chinh_sach_giao_hang` | 0.627 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | Y | Tôi ở Hà Nội. Tuy nhiên Sản phẩm Ipad Pro M4 lại chỉ còn tại Store Thanh Hóa. Khi thanh to… |
| 3 | Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành  | search | `chinh_sach_khui_hop_apple` | 0.570 | chinh_sach_khui_hop_apple/quy_dinh_sao_luu_du_lieu/chinh_sach_giao_hang | Y | - Nghiêm cấm không được có bất kỳ hành vi thay đổi hình thức và tính toàn vẹn của sản phẩm… |
| 3 | Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành  | filter | `chinh_sach_khui_hop_apple` | 0.570 | chinh_sach_khui_hop_apple/chinh_sach_khui_hop_apple | Y | - Nghiêm cấm không được có bất kỳ hành vi thay đổi hình thức và tính toàn vẹn của sản phẩm… |
| 4 | Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 | search | `bieu_phi_bao_hanh_mo_rong` | 0.628 | bieu_phi_bao_hanh_mo_rong/chinh_sach_giao_hang/bieu_phi_bao_hanh_mo_rong | Y | * Sản phẩm áp dụng: Điện thoại/ máy tính bảng mới/ cũ. * Thời gian tham gia: 12 tháng. * Q… |
| 4 | Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 | filter | `bieu_phi_bao_hanh_mo_rong` | 0.628 | bieu_phi_bao_hanh_mo_rong/bieu_phi_bao_hanh_mo_rong/bieu_phi_bao_hanh_mo_rong | Y | * Sản phẩm áp dụng: Điện thoại/ máy tính bảng mới/ cũ. * Thời gian tham gia: 12 tháng. * Q… |
| 5 | Mua trả góp qua thẻ tín dụng tại Cellphones cần điều ki | search | `chinh_sach_giao_hang` | 0.794 | chinh_sach_giao_hang/huong_dan_mua_tra_gop/huong_dan_mua_tra_gop | Y | Các quy định khi giao nhận hàng: - Với các đơn hàng từ 10 triệu đồng trở lên, CellphoneS x… |
| 5 | Mua trả góp qua thẻ tín dụng tại Cellphones cần điều ki | filter | `huong_dan_mua_tra_gop` | 0.794 | huong_dan_mua_tra_gop/huong_dan_mua_tra_gop/huong_dan_mua_tra_gop | Y | - Ngân hàng liên kết trực tiếp CellphoneS: khách hàng tiến hành cà thẻ và điền mẫu đơn đăn… |

**Hit@3 (search)** = 5/5    **Hit@3 (filter)** = 5/5

## Strategy `custom_vn_policy`

- Total chunks: **74**  |  avg chunk length: **439** chars  |  index time: 2.7s

| # | Query | Mode | Top-1 doc | Top-1 score | Top-3 docs | Hit@3 | Top-1 chunk |
|---|-------|------|-----------|------------:|------------|:-----:|-------------|
| 1 | Cellphones.com.vn do công ty nào sở hữu và quy định chu | search | `tos` | 0.850 | tos/tos/bieu_phi_bao_hanh_mo_rong | Y | PHẦN I. QUY ĐỊNH CHUNG **1. Nguyên tắc chung:** - Website thương mại điện tử Cellphones.co… |
| 1 | Cellphones.com.vn do công ty nào sở hữu và quy định chu | filter | `tos` | 0.850 | tos/tos/tos | Y | PHẦN I. QUY ĐỊNH CHUNG **1. Nguyên tắc chung:** - Website thương mại điện tử Cellphones.co… |
| 2 | Phí giao hàng nội thành Hà Nội như thế nào? | search | `chinh_sach_giao_hang` | 0.615 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | Y | - Giao & lắp đặt (đối với hàng cồng kềnh/điện máy): + Điều hòa, máy giặt, máy lạnh, tủ lạn… |
| 2 | Phí giao hàng nội thành Hà Nội như thế nào? | filter | `chinh_sach_giao_hang` | 0.615 | chinh_sach_giao_hang/chinh_sach_giao_hang/chinh_sach_giao_hang | Y | - Giao & lắp đặt (đối với hàng cồng kềnh/điện máy): + Điều hòa, máy giặt, máy lạnh, tủ lạn… |
| 3 | Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành  | search | `chinh_sach_khui_hop_apple` | 0.607 | chinh_sach_khui_hop_apple/quy_dinh_sao_luu_du_lieu/chinh_sach_khui_hop_apple | Y | - Sản phẩm Apple bắt buộc khui (mở) hộp và kích hoạt bảo hành điện tử ngay tại cửa hàng ho… |
| 3 | Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành  | filter | `chinh_sach_khui_hop_apple` | 0.607 | chinh_sach_khui_hop_apple/chinh_sach_khui_hop_apple/chinh_sach_khui_hop_apple | Y | - Sản phẩm Apple bắt buộc khui (mở) hộp và kích hoạt bảo hành điện tử ngay tại cửa hàng ho… |
| 4 | Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 | search | `chinh_sach_giao_hang` | 0.694 | chinh_sach_giao_hang/bieu_phi_bao_hanh_mo_rong/chinh_sach_giao_hang | Y | Trường hợp Quý khách không cung cấp đầy đủ chứng từ trên, CellphoneS xin phép thu 8% hoặc … |
| 4 | Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 | filter | `bieu_phi_bao_hanh_mo_rong` | 0.616 | bieu_phi_bao_hanh_mo_rong/bieu_phi_bao_hanh_mo_rong/bieu_phi_bao_hanh_mo_rong | Y | + Máy rơi vỡ - vào nước : khách hàng được hỗ trợ tới 90% chi phí sửa chữa. + Nếu sản phẩm … |
| 5 | Mua trả góp qua thẻ tín dụng tại Cellphones cần điều ki | search | `huong_dan_mua_tra_gop` | 0.716 | huong_dan_mua_tra_gop/chinh_sach_giao_hang/huong_dan_mua_tra_gop | Y | + Mua trả góp bằng thẻ tín dụng trực tiếp tại các cửa hàng với các ngân hàng có liên kết t… |
| 5 | Mua trả góp qua thẻ tín dụng tại Cellphones cần điều ki | filter | `huong_dan_mua_tra_gop` | 0.716 | huong_dan_mua_tra_gop/huong_dan_mua_tra_gop/huong_dan_mua_tra_gop | Y | + Mua trả góp bằng thẻ tín dụng trực tiếp tại các cửa hàng với các ngân hàng có liên kết t… |

**Hit@3 (search)** = 5/5    **Hit@3 (filter)** = 5/5

## Summary

| Strategy | # chunks | avg chunk len | Hit@3 (search) | Hit@3 (filter) |
|----------|---------:|--------------:|---------------:|---------------:|
| `fixed_size_300` | 123 | 294 | 4/5 | 5/5 |
| `by_sentences_3` | 67 | 485 | 4/5 | 5/5 |
| `recursive_300` | 154 | 210 | 4/5 | 5/5 |
| `structure_aware_600` | 60 | 542 | 5/5 | 5/5 |
| `custom_vn_policy` | 74 | 439 | 5/5 | 5/5 |

