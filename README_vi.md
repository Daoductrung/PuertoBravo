# Puerto Bravo: Ley del Asfalto

**Ngôn ngữ của tài liệu này:** [Español](README.md) · [English](README_en.md) · Tiếng Việt

> *Tài liệu này cũng có bản tiếng Tây Ban Nha ([Español](README.md)) và tiếng Anh ([English](README_en.md)).*

Trò chơi âm thanh thế giới mở, hỗ trợ tiếng Việt, tiếng Anh và tiếng Tây Ban Nha, hoàn toàn tiếp cận. Trò chơi được trải nghiệm hoàn toàn bằng thính giác: sử dụng bàn phím hoặc tay cầm Xbox / PlayStation, kết hợp cùng trình đọc màn hình (NVDA, JAWS hoặc giọng đọc Windows). Bạn hoàn toàn không cần nhìn vào màn hình để chơi.

Đây là một trò chơi nguyên bản. Thành phố, cốt truyện, các nhân vật và âm nhạc đều là sáng tạo riêng của tác phẩm.

Tài liệu này gồm bốn phần:

1. [Dành cho người chơi](#1-dành-cho-người-chơi): giới thiệu trò chơi và những trải nghiệm thế giới mở.
2. [Dành cho lập trình viên](#2-dành-cho-lập-trình-viên): thiết lập môi trường phát triển, kiểm thử, đóng gói và phát hành.
3. [Tạo bản mod](#3-tạo-bản-mod): mở rộng trò chơi với nội dung của riêng bạn.
4. [Gói âm thanh và âm nhạc](#4-gói-âm-thanh-và-âm-nhạc): tùy biến và thay đổi âm thanh trong trò chơi.

---

## Lời ngỏ về âm thanh

Tôi muốn thẳng thắn chia sẻ với bất kỳ ai đã đọc đến đây: Tôi là một lập trình viên, và âm thanh vốn không phải là thế mạnh của tôi. Do hạn chế về thời gian cũng như chuyên môn âm thanh, phần lớn các âm thanh trong trò chơi đều do chương trình tự tổng hợp hoặc được lấy từ các trang web cung cấp bản thu miễn phí bản quyền. Tôi biết chúng còn nhiều thiếu sót, mà đối với một trò chơi âm thanh thì âm thanh gần như là tất cả: với những âm thanh chất lượng cao, được lựa chọn bởi những người am hiểu âm thanh và gắn bó với trò chơi, Puerto Bravo chắc chắn sẽ hoàn thiện hơn rất nhiều.

Đó là lý do vì sao tôi luôn sẵn sàng đón nhận mọi sự hợp tác đóng góp gói âm thanh, dù là gói âm thanh hoàn chỉnh hay chỉ một vài âm thanh đơn lẻ. Nếu bạn muốn chung tay đóng góp:

- Cẩm nang hướng dẫn `data\docs\cambiar_sonidos_vi.html` (cũng có bản tiếng Anh `cambiar_sonidos_en.html` và tiếng Tây Ban Nha `cambiar_sonidos_es.html`) giải thích rõ từng âm thanh là gì, ý nghĩa khi nghe thấy, độ dài chuẩn của bản gốc và cách tạo một gói âm thanh. Mục [Gói âm thanh và âm nhạc](#4-gói-âm-thanh-và-âm-nhạc) tóm tắt các điểm chính.
- Các bản thu âm phải có thể chia sẻ hợp pháp cùng trò chơi: do chính bạn thu âm, hoặc dưới giấy phép mở tự do (CC0 hoặc tương đương), ghi rõ nguồn gốc xuất xứ của từng âm thanh.
- Để gửi đóng góp cho tôi, hãy mở một [GitHub issue](https://github.com/hxebolax/PuertoBravo/issues) kèm liên kết tải gói âm thanh (hoặc đính kèm tệp ZIP nếu dung lượng cho phép), hoặc nhắn tin cho tôi trên Mastodon tại [@HXeBoLaX](https://comunidad.nvda.es/@HXeBoLaX). Nếu bạn sử dụng Git, bạn hoàn toàn có thể gửi pull request với thư mục gói âm thanh riêng đặt trong `data\sonidos`.

Mọi sự giúp đỡ, dù là nhỏ nhất, đều vô cùng quý giá. Xin chân thành cảm ơn bạn trước.

## Về bản bản địa hóa tiếng Việt

Phiên bản tiếng Việt của trò chơi (toàn bộ menu, cốt truyện, cẩm nang hướng dẫn và tài liệu README này) được xây dựng và rà soát kỹ lưỡng nhằm mang đến trải nghiệm tiếp cận trọn vẹn và tự nhiên nhất cho cộng đồng người chơi khiếm thị Việt Nam.

Mọi ý kiến đóng góp sửa đổi hay hoàn thiện đều rất được hoan nghênh:

- Để báo lỗi dịch thuật hay đề xuất cải tiến, hãy mở một [GitHub issue](https://github.com/hxebolax/PuertoBravo/issues) mô tả rõ nơi xuất hiện và nội dung nên sửa lại, hoặc nhắn tin cho tôi trên Mastodon tại [@HXeBoLaX](https://comunidad.nvda.es/@HXeBoLaX).
- Nếu bạn muốn dịch trò chơi sang một ngôn ngữ khác, cẩm nang hướng dẫn giải thích quy trình dịch trong mục "Dịch trò chơi sang ngôn ngữ khác" (`data\docs\manual_vi.html` hoặc `manual_en.html`). Mỗi ngôn ngữ là một thư mục trong `data\idiomas`.
- Nếu bạn sử dụng Git, việc gửi Pull Request luôn luôn được chào đón.

## Tài liệu này bằng các ngôn ngữ khác

Mỗi ngôn ngữ có tệp tài liệu riêng đặt ngay cạnh tệp này, với mã hai chữ cái của ngôn ngữ ở cuối tên tệp, tương tự như các tài liệu hướng dẫn trong trò chơi: `README_en.md` là tiếng Anh, `README_vi.md` là tiếng Việt, và `README_it.md` sẽ là tiếng Ý. Khi dịch README sang ngôn ngữ mới, hãy thêm liên kết vào dòng ngôn ngữ ở đầu tất cả các tệp README hiện có.

---

## 1. Dành cho người chơi

### Cốt truyện

Bạn chọn một nhân vật có sẵn, hoặc tự tạo nhân vật của riêng mình với tên gọi, kỹ năng và ưu thế khởi đầu, đồng thời quyết định cách trò chơi xưng hô với bạn (nam hay nữ). Với nhân vật mặc định đầu tiên, bạn tên là Dani Roca và vừa mới ra tù sau ba năm bóc lịch vì một vụ trộm mà bạn không hề thực hiện. Bạn trở về thành phố quê hương Puerto Bravo, nơi giờ đây đã nằm dưới sự thao túng của doanh nhân Octavio Belmonte. Kể từ giây phút này, hãy sống theo cách bạn muốn: lần theo manh mối cốt truyện, kiếm sống lương thiện, gây dựng tên tuổi trong giới giang hồ đường phố hoặc chỉ đơn giản là thảnh thơi câu cá. Trò chơi không bao giờ ép buộc bạn phải làm bất cứ điều gì.

### Cách chơi hoàn toàn không cần thị giác

Mọi diễn biến xảy ra trong trò chơi đều có âm thanh riêng định vị trong không gian xung quanh bạn: âm thanh bên phải phát ra ở tai phải, âm thanh phía sau nghe trầm đục hơn. Đó là lý do bạn bắt buộc phải đeo tai nghe stereo. Ngoài ra bạn có rất nhiều công cụ hỗ trợ, tất cả đều là tùy chọn:

- Phím thông báo vị trí: cho biết tên đường, nằm giữa hai đại lộ nào, thuộc khu phố nào và bạn đang nhìn về hướng nào.
- Máy quét phương hướng hoạt động như cây gậy định vị: kiểm tra phía trước, phía sau, hai bên có gì và bức tường cách bao nhiêu mét.
- Ra-đa quét các mục tiêu xung quanh, thông báo khoảng cách và phương hướng, phát âm thanh định vị từ chính vị trí của vật thể.
- GPS dẫn đường bằng giọng nói, kết hợp tín hiệu âm thanh định hướng tới bất kỳ địa điểm nào trong mọi thị trấn.
- Khám phá bản đồ giúp làm quen với các con phố mà không cần phải di chuyển nhân vật.
- Tự động đi bộ và lái xe tự động theo GPS: nhân vật hoặc xe sẽ tự đi theo lộ trình trong khi bạn lắng nghe xung quanh.
- Lái xe có hỗ trợ: xe tự bám đúng làn đường; bạn chỉ cần quyết định tốc độ và ngã rẽ.
- Đèn giao thông phát âm thanh báo hiệu, tiếng bước chân thay đổi chân thực theo từng bề mặt địa hình và mỗi loại địa điểm đều có âm thanh đặc trưng riêng.
- Hai chế độ trợ giúp giúp bạn thảnh thơi khám phá: không nhận sát thương và không bị cảnh sát truy đuổi.

### Thế giới mở trong trò chơi

- Chín bản đồ chuẩn đi kèm: các thành phố Puerto Bravo, San Lucero và Monteferro; các thị trấn Villaseca, Cala Brava và Fuentefría; Đảo Rùa (Isla Tortuga), Bãi ngầm Hải Vương (Plataforma Neptuno) và Biển Phía Tây (Mar de Poniente) nơi bạn có thể lái thuyền ra khơi. Các bản mod đi kèm bổ sung thêm ba thị trấn và một hòn đảo mới.
- Hơn 300 địa điểm tiêu chuẩn: nhà ở, cửa hàng, ngân hàng, xưởng sửa chữa, sòng bạc, phòng tập thể hình, rạp chiếu phim, bệnh viện, cầu cảng, sân bay trực thăng, trạm xe điện, ga xe lửa, sân bay và các công trình biểu tượng — mỗi nơi đều có âm thanh và mô tả riêng biệt. Hầu hết các địa điểm và nhà cửa đều có thể bước vào trong và khám phá từng phòng.
- 75 nhiệm vụ tiêu chuẩn trải dài từ cốt truyện chính, các nhánh truyện phụ và năm bài hướng dẫn chơi được, cùng các công việc kiếm sống lặp lại không giới hạn. Các bản mod bổ sung thêm gần 70 nhiệm vụ khác. Một số nhiệm vụ đòi hỏi hoàn toàn bằng thính giác (lần theo tiếng bước chân, cảnh giới, đột nhập không tiếng động, đua xe), và các quyết định bạn đưa ra sẽ thay đổi diễn biến tiếp theo: bốn quyết định mở ra các nhánh rẽ khác nhau với tổng cộng 10 kết thúc.
- 39 phương tiện: ô tô, xe máy, xe đạp, xe tải, xe cứu thương / cảnh sát, thuyền buồm / ca-nô, trực thăng và máy bay hạng nhẹ. 22 loại vũ khí, hỗ trợ gắn ống giảm thanh và hộp tiếp đạn mở rộng.
- Giao thông công cộng: mạng lưới xe điện với các trạm dừng tại mọi khu phố, đường tàu hỏa kết nối giữa các thị trấn, xe buýt, taxi và các chuyến bay chở khách với hành trình thực tế.
- Bạn có thể lái thuyền vượt biển, cũng như bơi lội và lặn sâu dưới làn nước.
- Hệ thống cảnh sát với 5 cấp độ truy nã, chu kỳ ngày đêm, mưa bão, giao thông có đèn tín hiệu và người đi bộ đông đúc.

### Những hoạt động bạn có thể trải nghiệm

- Con đường lương thiện: trung tâm giới thiệu việc làm, các nghề nghiệp có cơ hội thăng tiến (lái taxi, lái xe cứu thương, xe buýt, lính cứu hỏa, lái xe cẩu, người giao hàng, tài xế xe tải chở hàng, người bán kem, ngư dân), các khóa học nâng cao kỹ năng, công việc tình nguyện và tự mở cơ sở kinh doanh riêng.
- Con đường tội phạm đường phố: làm nhiệm vụ ngầm, nhận hợp đồng phi vụ, cướp xe theo đơn đặt hàng, cướp ngân hàng và chiến tranh tranh giành lãnh bàn giữa các băng nhóm.
- Giải trí: đua xe đường phố và đua thuyền buồm, sòng bạc casino, chơi lô tô bingo, xổ số, bài xì dách bảy rưỡi, cờ domino, trò đoán đồng xu, đấm bốc boxing, trường bắn tập bắn, câu cá, săn tìm kho báu dưới đáy biển, rạp chiếu phim, trò chơi điện tử xèng arcade và thị trường chứng khoán.
- Mua nhà có gara riêng, nuôi một chú chó trung thành bầu bạn và đánh hơi tìm đồ vật, thuê vệ sĩ bảo vệ, lập băng nhóm riêng, phòng thủ các khu phố, độ xe nâng cấp tại xưởng cơ khí, mở khóa thành tựu và rèn luyện kỹ năng qua quá trình trải nghiệm.
- Trò chuyện với bất kỳ người đi bộ nào trên đường phố: mỗi người đều có họ tên, nghề nghiệp và tính cách riêng. Bạn có thể hỏi đường, mời họ đi uống cà phê, kết bạn hoặc gõ bất cứ điều gì bạn muốn nói. Chế độ tùy chọn cho phép họ phản hồi bằng trí tuệ nhân tạo: mô hình miễn phí chạy ngoại tuyến không cần internet, Google AI Studio, OpenAI, Anthropic hoặc các dịch vụ tương thích khác.
- Giọng lồng tiếng trong các phân cảnh: mọi nhân vật trong cốt truyện và các bản mod đi kèm đều có giọng nói riêng biệt được tổng hợp bởi máy tính. Họ gọi đúng tên nhân vật bạn đang chơi và xưng hô chuẩn xác theo giới tính nam/nữ; với nhân vật tự tạo, các câu thoại nhắc tên bạn sẽ được máy tính của bạn tự động tổng hợp. Bất kỳ ai cũng có thể tự thu âm và thay thế giọng nói.
- Hai công cụ âm thanh: công cụ âm thanh truyền thống và công cụ âm thanh vòm hai tai (binaural), mô phỏng tiếng vang âm học chân thực riêng cho từng không gian địa điểm.
- Khi không dùng AI, hệ thống cơ sở dữ liệu hơn 1.100 câu thoại thuộc gần 70 chủ đề (`juego/respuestas.py`) sẽ phản hồi tự nhiên theo đúng tính cách của từng người.
- Thành phố biến đổi không ngừng: mỗi ngày đều có sự kiện khác nhau (ngày giảm giá, ngày họp chợ, lễ hội, đình công, kỳ nghỉ lễ), kéo theo sự thay đổi về giá cả hàng hóa, mật độ người dân và xe cộ. Không có hai màn chơi nào hoàn toàn giống nhau.
- Mức độ chân thực tùy chỉnh: đói, khát, buồn ngủ và tắm rửa vệ sinh; nhiên liệu và các trạm xăng; hỏng hóc xe, thủng lốp và bảo dưỡng định kỳ; luật lệ giao thông với hệ thống vé phạt và bằng lái xe trừ điểm.
- Chơi trên máy chủ nhiều người: thế giới sống động kết nối người chơi thực, thành lập băng đảng, tranh chấp lãnh địa, sở hữu nhà cửa kinh doanh, chia sẻ chung hệ thống giao thông, người đi bộ và cảnh sát. Bất kỳ ai cũng có thể tự mở máy chủ: mã nguồn máy chủ đi kèm sẵn trong trò chơi, có giao diện điều khiển tiếp cận và cẩm nang hướng dẫn từng bước.
- Đài phát thanh radio: khi bạn bước xuống xe đài sẽ tự tạm dừng và tiếp tục phát đúng đoạn đó khi bạn lên xe; nếu mua máy nghe nhạc cầm tay và tai nghe bạn có thể nghe đài khi đi bộ.
- Chơi cùng bạn bè không cần máy chủ ngoài: chính trò chơi của bạn sẽ làm máy chủ tiếp đón, có hoặc không có mật khẩu, và bạn chỉ cần gửi địa chỉ cho bạn bè. Bạn có thể nghe thấy nhau trong không gian, tìm nhau qua ra-đa và GPS, nhắn tin trò chuyện, ngồi chung trên một chiếc xe hơi, tổ chức đua xe cá cược và lập đội cùng đi giao hàng.
- Bảy kênh radio với âm nhạc nguyên bản, một kênh tin tức bình luận về chính những việc bạn làm trong thành phố và một kênh dành riêng để phát các bài hát của bạn. Âm nhạc môi trường tự biến chuyển theo tình huống.
- Chế độ nội dung người lớn (tùy chọn, mặc định tắt): các mối quan hệ tình cảm, cuộc sống về đêm, các chất kích thích và hệ lụy của chúng, được truyền tải tinh tế không có cảnh dung tục.

### Yêu cầu hệ thống và bắt đầu trải nghiệm

- Hệ điều hành Windows 10 hoặc 11 (64-bit).
- Tai nghe âm thanh nổi (stereo headphones).
- Một trình đọc màn hình đang chạy, chẳng hạn như NVDA hoặc JAWS. Nếu không có, trò chơi sẽ tự động phát âm bằng giọng đọc tích hợp sẵn của Windows.

Hãy tải về phiên bản mới nhất, giải nén thư mục vào bất kỳ nơi nào bạn thích và chạy tập tin `PuertoBravo.exe`. Trò chơi không cần cài đặt: đây là bản portable độc lập. Trong trò chơi, phím `F1` sẽ nhắc bạn các phím tắt bất cứ lúc nào, và menu chính mở cẩm nang hướng dẫn đầy đủ nằm tại `data\docs\manual_vi.html` (và bản tiếng Anh `manual_en.html`, tiếng Tây Ban Nha `manual_es.html`), có thể điều hướng dễ dàng theo các tiêu đề. Trò chơi tự động nhận diện ngôn ngữ Windows và bạn có thể thay đổi trong Tùy chọn, Ngôn ngữ.

Nếu gặp sự cố, trò chơi sẽ lưu nhật ký của từng phiên trong thư mục `data\logs`, hoàn toàn không chứa thông tin cá nhân: hãy nén thư mục của phiên bị lỗi thành tệp ZIP và đính kèm vào một [GitHub issue](https://github.com/hxebolax/PuertoBravo/issues), hoặc gửi qua Mastodon cho tác giả [@HXeBoLaX](https://comunidad.nvda.es/@HXeBoLaX). Cẩm nang hướng dẫn có giải thích chi tiết.

Trò chơi tự cập nhật từ ngay bên trong menu Tùy chọn. Bạn có thể chọn nguồn tải: máy chủ trò chơi, GitHub, cả hai hoặc địa chỉ riêng của bạn. Các màn chơi đã lưu, tùy chọn cài đặt, âm nhạc và bản mod của bạn sẽ được giữ nguyên vẹn.

---

## 2. Dành cho lập trình viên

### Yêu cầu môi trường

- Windows 10 hoặc 11 (64-bit).
- Python 3.13 trở lên. Dự án được phát triển chính với Python 3.15.

### Các bước khởi đầu

Mọi thao tác quản trị và biên dịch đều được thực hiện qua các tệp kịch bản lệnh `.bat` ở thư mục gốc:

```bat
entorno.bat    :: tạo môi trường ảo .venv và cài đặt các thư viện phụ thuộc
jugar.bat      :: mở trò chơi trực tiếp từ mã nguồn
editor.bat     :: mở trình chỉnh sửa bản mod (EditorMods)
probar.bat     :: thực thi toàn bộ bài kiểm thử tự động (pytest)
compilar.bat   :: biên dịch ra thư mục dist\PuertoBravo (portable, sẵn sàng phân phối)
publicar.bat   :: nén ZIP, ký số và phát hành bản dựng
```

Chi tiết: `entorno.bat` tạo môi trường ảo `.venv` và cài đặt các thư viện cần thiết; `jugar.bat` chạy game từ mã nguồn; `editor.bat` mở trình sửa mod; `probar.bat` chạy kiểm thử tự động; `compilar.bat` biên dịch thư mục `dist\PuertoBravo` độc lập; `publicar.bat` nén, ký số và xuất bản.

Các thư viện phụ thuộc (`requirements.txt`): pygame-ce, numpy, sounddevice, soundfile, accessible-output2, wxPython, cx_Freeze và pytest. Riêng tính năng AI không cần bất kỳ gói ngoài nào: trò chơi giao tiếp trực tiếp qua giao thức HTTPS bằng thư viện chuẩn của Python (`juego/ia.py`), tự động truy vấn danh sách mô hình và chọn mô hình tiết kiệm nhất.

Kho lưu trữ đã bao gồm đầy đủ dữ liệu âm thanh: các âm thanh mặc định và bốn gói âm thanh trong `data/sonidos` (gói Envolvente được tạo bằng `herramientas/crear_pack_envolvente.py`), âm nhạc radio trong `data/radio` và nhạc nền môi trường trong `data/musica`. Nếu thiếu bất kỳ âm thanh mặc định nào, trò chơi sẽ tự động tái tạo lại khi khởi động.

### Cấu trúc mã nguồn

- `juego/`: mã nguồn chính của trò chơi. `app.py` là vòng lặp chính và ngăn xếp màn hình; `partida.py` lắp ráp phiên chơi từ các mô-đun chuyên biệt (lái xe, chiến đấu, nhiệm vụ, nghề nghiệp, đời sống lương thiện, đối thoại, chơi mạng, sự kiện ngẫu nhiên hàng ngày...); `sintesis.py` tạo âm thanh mặc định; `audio.py` là bộ trộn âm thanh định vị không gian.
- `editor/`: trình chỉnh sửa bản mod, xây dựng bằng wxPython.
- `herramientas/`: các công cụ sinh âm thanh, tài liệu hướng dẫn, kiểm tra và bảo vệ bản dựng, đóng gói âm thanh, quản lý mod và phát hành.
- `pruebas/`: hệ thống kiểm thử tự động sử dụng pytest.
- `data/datos/`: bản đồ, địa điểm, nhiệm vụ, vũ khí, phương tiện, nhân vật và người đi bộ cùng các kẻ thù, lưu dưới định dạng JSON.
- `data/mods/`: các bản mod đi kèm sẵn, định dạng JSON dễ đọc.
- `data/docs/`: tài liệu hướng dẫn phân phối cùng trò chơi dành cho người chơi.
- `desarrollo/`: tài liệu kỹ thuật nội bộ (như cấu trúc tệp mod).

### Máy chủ trực tuyến (Dedicated Server)

Máy chủ (`servidor/`) chỉ sử dụng thư viện chuẩn của Python và hoạt động độc lập không cần trò chơi, chạy tốt trên Windows, Linux, macOS, NAS hoặc Docker. Máy chủ không chứa sẵn nội dung trò chơi: bản đồ, vũ khí, phương tiện và nhiệm vụ sẽ được truyền lên từ người chơi đầu tiên tham gia phiên bản đó (được ký số xác thực bởi nhà phát hành), cho phép các phiên bản game khác nhau cùng chơi chung trên một máy chủ. Các tùy chọn máy chủ được quản lý tập trung tại `servidor/opciones.py`. Bảng điều khiển máy chủ (`panel_servidor/`, `servidor_panel.py`) là cửa sổ wxPython kế thừa tính năng tiếp cận của trình sửa mod. Khi phát triển, máy chủ được khởi chạy bằng `servidor.bat` hoặc `servidor_panel.bat`. Cẩm nang dành cho quản trị viên là `data\docs\servidor.html`. Tập lệnh `herramientas\prueba_servidor_real.py` khởi chạy máy chủ thực tế trong tiến trình riêng và kết nối 10 máy khách mô phỏng qua mạng.

### Kiểm thử tự động

Tập lệnh `probar.bat` thực thi toàn bộ bộ kiểm thử. Các bài kiểm thử điều khiển trò chơi tương tự như người thật bằng cách gửi phím và khung hình: trải nghiệm từng nhiệm vụ, đi khắp các bản đồ theo GPS, duyệt qua mọi menu và địa điểm, mô phỏng 20 ngày chơi với thời gian tua nhanh, kết nối hai trò chơi với nhau, điều khiển tay cầm ảo và kiểm tra khả năng tiếp cận của trình sửa mod. Bộ kiểm thử cũng sẽ báo lỗi nếu có âm thanh mới nào bị thiếu mô tả hoặc phím tắt nào chưa có tài liệu hướng dẫn. Quá trình kiểm thử hoàn toàn không yêu cầu kết nối mạng hay card âm thanh vật lý.

### Biên dịch và phát hành

`compilar.bat` sử dụng cx_Freeze và xuất ra thư mục portable `dist\PuertoBravo` chứa `PuertoBravo.exe` và `EditorMods.exe`. Trước khi biên dịch, tập lệnh tự động tạo lại các bản mod có sẵn, bổ sung các âm thanh còn thiếu và cập nhật các tài liệu hướng dẫn. Khi hoàn tất:

- Dữ liệu trò chơi được bảo vệ: mỗi tệp JSON được nén, mã hóa và ký số, đổi phần mở rộng (`.pbd` dữ liệu, `.pbm` mod, `.pbs` file lưu, `.pbc` cấu hình). Mã nguồn hỗ trợ đọc cả hai định dạng nên trong quá trình phát triển mọi thứ vẫn là JSON văn bản rõ ràng.
- Tự động kiểm tra bản dựng: đảm bảo thư mục đầy đủ, được bảo vệ và sạch sẽ (không chứa file lưu thử, cấu hình cá nhân, nhật ký hay tài liệu nội bộ).

Việc cập nhật trò chơi được xác thực qua tệp `version.json` có chữ ký điện tử Ed25519, tuân thủ tiêu chuẩn RFC 8032. Bất kể tải từ máy chủ, GitHub hay nguồn riêng, chỉ những bản cập nhật có chữ ký hợp lệ từ khóa riêng của nhà phát hành mới được chấp nhận cài đặt.

### Khả năng tiếp cận và Bản địa hóa (i18n)

Puerto Bravo được thiết kế chuẩn mực cho khả năng tiếp cận và bản địa hóa:
- Tự động nhận diện trình đọc màn hình qua `accessible-output2` (NVDA, JAWS) hoặc phát âm qua Windows Speech SAPI / OneCore nếu không có trình đọc màn hình chuyên dụng.
- Cửa sổ trò chơi hiển thị trực quan thông điệp phát âm gần nhất bằng chữ lớn, độ tương phản cao dành cho người chơi còn một phần thị lực hoặc người sáng mắt cùng xem.
- Hệ thống i18n (`juego/i18n.py`) tách biệt toàn bộ chuỗi văn bản vào danh mục ngôn ngữ (`data/idiomas/<mã>/textos.json`), hỗ trợ phân biệt biến thể ngữ pháp nam/nữ (`[anh|chị]`, `[cậu|cô]`), các mẫu định dạng chuỗi có tên, và nạp động tài liệu theo mã ngôn ngữ (`data/docs/<tên>_<mã>.html`).

---

## 3. Tạo bản mod

Bản mod là một bản mở rộng của trò chơi: bạn có thể thêm địa điểm mới, nhiệm vụ, phương tiện, vũ khí hoặc toàn bộ thị trấn mới.

- Để tạo mod: chạy `EditorMods.exe` nằm ngay cạnh tệp chạy trò chơi. Trình chỉnh sửa được thiết kế tiếp cận hoàn toàn cho người khiếm thị sử dụng trình đọc màn hình.
- Phím `F1` trong trình chỉnh sửa mở cẩm nang hướng dẫn chi tiết, và `Control H` giải thích công dụng của từng trường dữ liệu bạn đang chọn.
- Mỗi bản mod là một tệp riêng đặt trong thư mục `data\mods`. Trò chơi sẽ tự động tải các bản mod khi khởi động.
- Để cài một bản mod: chép tệp mod vào thư mục `data\mods`.
- Để tắt hoặc xóa mod: xóa tệp khỏi thư mục hoặc nhấn `Control M` trong trình chỉnh sửa để vô hiệu hóa.

---

## 4. Gói âm thanh và âm nhạc

Bạn có thể thay đổi âm thanh và âm nhạc trong trò chơi theo sở thích của mình:

- Trò chơi đi kèm sẵn 5 gói âm thanh trong thư mục `data\sonidos`:
  - `por_defecto`: gói âm thanh mặc định được chương trình tự tổng hợp.
  - `realista`: gói âm thanh chân thực từ các bản thu thực tế.
  - `alternativo`: gói âm thanh biến thể.
  - `retro`: gói âm thanh mang phong cách cổ điển.
  - `envolvente`: gói âm thanh vòm không gian mở rộng.
- Bạn có thể chuyển đổi giữa các gói âm thanh trong trò chơi: vào mục **Tùy chọn** -> **Âm thanh** -> **Gói âm thanh**.
- Tự thêm nhạc của bạn: sao chép các tệp âm thanh định dạng `.ogg`, `.mp3` hoặc `.wav` vào thư mục `data\radio\mi_musica`. Trong trò chơi, bật đài radio và chuyển sang kênh **Nhạc của tôi** để thưởng thức danh sách bài hát yêu thích của bạn khi lái xe hoặc đi dạo.
- Chi tiết về cách tạo một gói âm thanh mới được hướng dẫn cụ thể trong cẩm nang `data\docs\cambiar_sonidos_vi.html` (hoặc `cambiar_sonidos_en.html`).

---

## Giấy phép bản quyền

Dự án phát hành dưới **Giấy phép MIT (MIT License)**: Bạn có toàn quyền sử dụng, sửa đổi, chia sẻ và phân phối bất kỳ phần nào của trò chơi, với điều kiện duy nhất là giữ nguyên thông tin bản quyền và thông báo giấy phép gốc. Chi tiết xem trong tệp `LICENSE`.
