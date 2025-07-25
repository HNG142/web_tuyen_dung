// Đảm bảo code chạy sau khi toàn bộ tài liệu HTML đã được tải
document.addEventListener('DOMContentLoaded', () => {
    // Lấy các phần tử HTML cần thiết bằng ID
    const mainApp = document.getElementById('main-app');
    const authSection = document.getElementById('auth-section');
    const userEmailSpan = document.getElementById('user-email');
    const authMessage = document.getElementById('auth-message');
    const logoutButton = document.getElementById('logout-button');
    
    let currentSessionId = null; // Biến để lưu ID phiên chatbot hiện tại
    let currentTestId = null; // Biến để lưu ID bài kiểm tra kỹ năng hiện tại
    let currentTestQuestions = []; // Lưu các câu hỏi của bài kiểm tra hiện tại

    // --- Hàm tiện ích ---
    // Hàm này được dùng để ẩn/hiện các tab nội dung
    function openTab(tabName) {
        // Ẩn tất cả các tab nội dung
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        // Hiển thị tab được chọn
        document.getElementById(tabName).classList.add('active');

        // Cập nhật trạng thái "active" cho nút tab
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        document.querySelector(`.tab-button[onclick="openTab('${tabName}')"]`).classList.add('active');
    }
    window.openTab = openTab; // Đặt hàm này vào global scope để HTML có thể gọi `onclick`

    // Hàm lấy token xác thực từ Local Storage của trình duyệt
    function getToken() {
        return localStorage.getItem('access_token');
    }

    // Hàm kiểm tra trạng thái đăng nhập và hiển thị giao diện phù hợp
    function checkAuth() {
        if (getToken()) { // Nếu có token (đã đăng nhập)
            authSection.style.display = 'none'; // Ẩn phần đăng nhập/đăng ký
            mainApp.style.display = 'block'; // Hiện phần ứng dụng chính
            userEmailSpan.textContent = localStorage.getItem('user_email'); // Hiển thị email người dùng
            openTab('upload'); // Mở tab "Nộp CV/JD" mặc định
        } else { // Nếu không có token (chưa đăng nhập)
            authSection.style.display = 'block'; // Hiện phần đăng nhập/đăng ký
            mainApp.style.display = 'none'; // Ẩn phần ứng dụng chính
        }
    }

    // Hàm chung để gửi yêu cầu đến API backend của FastAPI
    async function fetchData(url, options = {}) {
        const token = getToken();
        if (token) { // Nếu có token, thêm vào header Authorization
            options.headers = {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            };
        }
        const response = await fetch(url, options); // Gửi yêu cầu HTTP
        if (!response.ok) { // Nếu có lỗi từ server (ví dụ: 401 Unauthorized)
            if (response.status === 401 || response.status === 403) {
                alert('Phiên đăng nhập đã hết hạn hoặc không có quyền. Vui lòng đăng nhập lại.');
                localStorage.clear(); // Xóa token cũ
                checkAuth(); // Chuyển về giao diện đăng nhập
            }
            // Ném lỗi để các hàm gọi có thể bắt và xử lý
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        return response.json(); // Trả về dữ liệu JSON từ phản hồi
    }

    // --- Xử lý Xác thực ---
    // Đăng ký
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault(); // Ngăn chặn form gửi đi theo cách truyền thống
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        try {
            await fetchData('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }) // Chuyển dữ liệu thành chuỗi JSON
            });
            authMessage.textContent = 'Đăng ký thành công! Bạn có thể đăng nhập.';
            authMessage.style.color = 'green';
        } catch (error) {
            authMessage.textContent = 'Đăng ký thất bại: ' + error.message;
            authMessage.style.color = 'red';
            console.error('Registration error:', error);
        }
    });

    // Đăng nhập
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        try {
            // FastAPI với OAuth2PasswordRequestForm yêu cầu dữ liệu dạng form-urlencoded
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const data = await fetchData('/api/auth/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData.toString()
            });
            localStorage.setItem('access_token', data.access_token); // Lưu token vào Local Storage
            localStorage.setItem('user_email', email); // Lưu email để hiển thị
            authMessage.textContent = 'Đăng nhập thành công!';
            authMessage.style.color = 'green';
            checkAuth(); // Cập nhật giao diện
        } catch (error) {
            authMessage.textContent = 'Đăng nhập thất bại: ' + error.message;
            authMessage.style.color = 'red';
            console.error('Login error:', error);
        }
    });

    // Đăng xuất
    logoutButton.addEventListener('click', () => {
        localStorage.clear(); // Xóa tất cả dữ liệu lưu trữ
        checkAuth(); // Chuyển về giao diện đăng nhập
        authMessage.textContent = 'Bạn đã đăng xuất.';
        authMessage.style.color = 'initial';
    });

    // --- Xử lý tải lên CV/JD ---
    document.getElementById('upload-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const uploadStatus = document.getElementById('upload-status');
        const matchingResults = document.getElementById('matching-results');
        const matchScoreSpan = document.getElementById('match-score');
        const matchFeedbackP = document.getElementById('match-feedback');
        const cvSuggestionsUl = document.getElementById('cv-suggestions');

        uploadStatus.textContent = 'Đang xử lý... Vui lòng chờ vài giây để AI phân tích.';
        uploadStatus.style.color = 'blue';
        matchingResults.style.display = 'none'; // Ẩn kết quả cũ

        // Tạo FormData để gửi file và các trường văn bản
        const formData = new FormData();
        formData.append('full_name', document.getElementById('candidate-full-name').value);
        formData.append('email', document.getElementById('candidate-email').value);
        formData.append('applied_position', document.getElementById('candidate-position').value);
        formData.append('cv_file', document.getElementById('cv-file').files[0]);
        formData.append('jd_file', document.getElementById('jd-file').files[0]);

        try {
            const response = await fetchData('/api/candidates/upload-cv-jd', {
                method: 'POST',
                body: formData // Gửi FormData
            });

            uploadStatus.textContent = response.message;
            uploadStatus.style.color = 'green';

            // Hiển thị kết quả phân tích AI
            if (response.match_score !== undefined) {
                matchScoreSpan.textContent = response.match_score;
                matchFeedbackP.textContent = response.feedback;
                cvSuggestionsUl.innerHTML = ''; // Xóa gợi ý cũ
                response.suggestions.forEach(sug => {
                    const li = document.createElement('li');
                    li.textContent = sug;
                    cvSuggestionsUl.appendChild(li);
                });
                matchingResults.style.display = 'block'; // Hiện kết quả
            }
        } catch (error) {
            uploadStatus.textContent = 'Lỗi khi tải lên hoặc phân tích: ' + error.message;
            uploadStatus.style.color = 'red';
            console.error('Upload error:', error);
        }
    });

    // --- Xử lý Chatbot phỏng vấn AI ---
    const chatBox = document.getElementById('chat-box');
    const messagesDiv = document.getElementById('messages');
    const chatInput = document.getElementById('chat-input');
    const sendChatButton = document.getElementById('send-chat-button');
    const interviewStatus = document.getElementById('interview-status');
    const interviewCandidateIdInput = document.getElementById('interview-candidate-id');

    // Hàm thêm tin nhắn vào hộp chat
    function addMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender); // Thêm class 'user' hoặc 'bot'
        msgDiv.textContent = text;
        messagesDiv.appendChild(msgDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight; // Cuộn xuống cuối hộp chat
    }

    // Bắt đầu phỏng vấn
    document.getElementById('start-interview-button').addEventListener('click', async () => {
        const candidateId = interviewCandidateIdInput.value;
        if (!candidateId) {
            alert('Vui lòng nhập ID ứng viên để bắt đầu phỏng vấn.');
            return;
        }
        messagesDiv.innerHTML = ''; // Xóa tin nhắn cũ
        chatBox.style.display = 'block'; // Hiện hộp chat
        chatInput.disabled = true;
        sendChatButton.disabled = true;
        interviewStatus.textContent = 'Đang khởi tạo phỏng vấn...';

        try {
            const response = await fetchData(`/api/interview/start/${candidateId}`, {
                method: 'POST'
            });
            currentSessionId = response.session_id; // Lưu ID phiên
            addMessage('bot', response.first_message); // Hiển thị tin nhắn đầu tiên của bot
            chatInput.disabled = false; // Bật ô nhập liệu
            sendChatButton.disabled = false;
            interviewStatus.textContent = 'Phỏng vấn đã bắt đầu. Hãy nhập câu trả lời của bạn.';
            chatInput.focus(); // Đặt con trỏ vào ô nhập liệu
        } catch (error) {
            interviewStatus.textContent = 'Lỗi khi bắt đầu phỏng vấn: ' + error.message;
            interviewStatus.style.color = 'red';
            console.error('Start interview error:', error);
        }
    });

    // Gửi tin nhắn đến chatbot
    sendChatButton.addEventListener('click', async () => {
        const message = chatInput.value.trim();
        if (!message || !currentSessionId) return; // Không gửi nếu trống hoặc chưa có phiên

        addMessage('user', message); // Thêm tin nhắn của người dùng vào hộp chat
        chatInput.value = ''; // Xóa nội dung ô nhập liệu
        chatInput.disabled = true; // Vô hiệu hóa ô nhập liệu và nút gửi
        sendChatButton.disabled = true;
        interviewStatus.textContent = 'AI đang trả lời...';

        try {
            const response = await fetchData(`/api/interview/chat/${currentSessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });
            addMessage('bot', response.response); // Thêm phản hồi của bot vào hộp chat
            interviewStatus.textContent = '';
        } catch (error) {
            interviewStatus.textContent = 'Lỗi khi trò chuyện: ' + error.message;
            interviewStatus.style.color = 'red';
            console.error('Chat error:', error);
        } finally {
            chatInput.disabled = false; // Bật lại ô nhập liệu và nút gửi
            sendChatButton.disabled = false;
            chatInput.focus();
        }
    });
    // Gửi tin nhắn khi nhấn Enter
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatButton.click();
        }
    });

    // --- Xử lý Kiểm tra kỹ năng ---
    const quizContainer = document.getElementById('quiz-container');
    const questionsDisplay = document.getElementById('questions-display');
    const submitTestButton = document.getElementById('submit-test-button');
    const testResultsDiv = document.getElementById('test-results');

    // Bắt đầu bài kiểm tra
    document.getElementById('start-test-button').addEventListener('click', async () => {
        const candidateId = document.getElementById('test-candidate-id').value;
        const skillCategory = document.getElementById('test-skill-category').value;
        if (!candidateId || !skillCategory) {
            alert('Vui lòng nhập ID ứng viên và danh mục kỹ năng (ví dụ: Python).');
            return;
        }

        quizContainer.style.display = 'none'; // Ẩn quiz cũ
        questionsDisplay.innerHTML = ''; // Xóa câu hỏi cũ
        testResultsDiv.innerHTML = ''; // Xóa kết quả cũ
        submitTestButton.style.display = 'none';

        try {
            const response = await fetchData(`/api/tests/start/${candidateId}/${skillCategory}`, {
                method: 'POST'
            });
            currentTestId = response.test_id; // Lưu ID bài kiểm tra
            currentTestQuestions = response.questions; // Lưu các câu hỏi

            // Hiển thị từng câu hỏi
            response.questions.forEach((q, index) => {
                const qDiv = document.createElement('div');
                qDiv.classList.add('question-item');
                qDiv.innerHTML = `<p>${index + 1}. ${q.question_text}</p>`;
                q.options.forEach(option => {
                    qDiv.innerHTML += `
                        <label>
                            <input type="radio" name="question_${q.id}" value="${option}"> ${option}
                        </label><br>
                    `;
                });
                questionsDisplay.appendChild(qDiv);
            });

            quizContainer.style.display = 'block'; // Hiện khu vực quiz
            submitTestButton.style.display = 'block'; // Hiện nút nộp bài

        } catch (error) {
            alert('Lỗi khi bắt đầu kiểm tra kỹ năng: ' + error.message);
            console.error('Skill test start error:', error);
        }
    });

    // Nộp bài kiểm tra
    submitTestButton.addEventListener('click', async () => {
        const answers = [];
        currentTestQuestions.forEach(q => {
            // Tìm đáp án được chọn cho mỗi câu hỏi
            const selectedOption = document.querySelector(`input[name="question_${q.id}"]:checked`);
            if (selectedOption) {
                answers.push({
                    question_id: q.id,
                    selected_answer: selectedOption.value
                });
            }
        });

        if (!currentTestId) {
            alert('Không có bài kiểm tra đang hoạt động để nộp.');
            return;
        }

        try {
            const response = await fetchData(`/api/tests/submit/${currentTestId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(answers)
            });

            testResultsDiv.innerHTML = `<h3>Kết quả bài kiểm tra:</h3>
                                        <p>Điểm số: ${response.score} / ${response.total_questions}</p>`;
            submitTestButton.style.display = 'none'; // Ẩn nút nộp bài sau khi nộp
            
            // Lấy và hiển thị kết quả chi tiết
            const detailedResults = await fetchData(`/api/tests/results/${currentTestId}`);
            detailedResults.items.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.innerHTML = `<p><strong>Câu hỏi:</strong> ${item.question_text}</p>
                                     <p><strong>Trả lời của bạn:</strong> ${item.selected_answer || 'Không trả lời'}</p>
                                     <p><strong>Kết quả:</strong> <span style="color: ${item.is_correct ? 'green' : 'red'};">${item.is_correct ? 'Đúng' : 'Sai'}</span></p><hr>`;
                testResultsDiv.appendChild(itemDiv);
            });

        } catch (error) {
            alert('Lỗi khi nộp bài kiểm tra: ' + error.message);
            console.error('Skill test submit error:', error);
        }
    });

    // Tạo câu hỏi mới
    document.getElementById('create-question-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const questionText = document.getElementById('new-question-text').value;
        // Tách các lựa chọn bằng dấu phẩy
        const options = document.getElementById('new-question-options').value.split(',').map(o => o.trim());
        const correctAnswer = document.getElementById('new-question-correct').value;
        const skillCategory = document.getElementById('new-question-category').value;

        try {
            await fetchData('/api/tests/questions/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_text: questionText,
                    options: options,
                    correct_answer: correctAnswer,
                    skill_category: skillCategory
                })
            });
            alert('Câu hỏi đã được tạo thành công!');
            e.target.reset(); // Xóa form
        } catch (error) {
            alert('Lỗi khi tạo câu hỏi: ' + error.message);
            console.error('Create question error:', error);
        }
    });

    // --- Danh sách ứng viên & Chi tiết ---
    const candidatesTableBody = document.querySelector('#candidates-table tbody');
    const candidateDetailsDiv = document.getElementById('candidate-details');
    const sendOfferButton = document.getElementById('send-offer-button');
    let selectedCandidateForOffer = null; // Lưu ID ứng viên được chọn để gửi email

    // Hàm tải danh sách ứng viên (có thể tìm kiếm theo ID)
    async function loadCandidates(candidateId = null) {
        candidatesTableBody.innerHTML = ''; // Xóa bảng cũ
        candidateDetailsDiv.style.display = 'none'; // Ẩn chi tiết cũ
        let url = '/api/candidates/';
        if (candidateId) {
            url += candidateId; // Nếu có ID, truy vấn ứng viên cụ thể
        }

        try {
            const candidates = candidateId ? [await fetchData(url)] : await fetchData(url); // Nếu tìm kiếm 1, trả về mảng 1 phần tử
            candidates.forEach(candidate => {
                const row = candidatesTableBody.insertRow();
                row.innerHTML = `
                    <td>${candidate.id}</td>
                    <td>${candidate.full_name}</td>
                    <td>${candidate.email}</td>
                    <td>${candidate.applied_position || 'N/A'}</td>
                    <td><button data-id="${candidate.id}" class="view-details-button">Xem chi tiết</button></td>
                `;
            });
        } catch (error) {
            console.error('Lỗi khi tải danh sách ứng viên:', error);
            candidatesTableBody.innerHTML = '<tr><td colspan="5">Không thể tải danh sách ứng viên.</td></tr>';
        }
    }

    // Nút tìm kiếm ứng viên
    document.getElementById('search-candidates-button').addEventListener('click', () => {
        const searchId = document.getElementById('search-candidate-id').value;
        loadCandidates(searchId ? parseInt(searchId) : null); // Gọi hàm tải ứng viên
    });

    // Xử lý sự kiện click vào nút "Xem chi tiết"
    candidatesTableBody.addEventListener('click', async (e) => {
        if (e.target.classList.contains('view-details-button')) {
            const candidateId = e.target.dataset.id; // Lấy ID từ thuộc tính data-id
            selectedCandidateForOffer = candidateId; // Lưu ID để gửi thư mời

            try {
                const candidate = await fetchData(`/api/candidates/${candidateId}`);
                // Hiển thị thông tin cơ bản
                document.getElementById('detail-id').textContent = candidate.id;
                document.getElementById('detail-name').textContent = candidate.full_name;
                document.getElementById('detail-email').textContent = candidate.email;
                document.getElementById('detail-position').textContent = candidate.applied_position || 'N/A';

                // Tải và hiển thị Kết quả phù hợp CV/JD
                const matchResultsDiv = document.getElementById('detail-match-results');
                matchResultsDiv.innerHTML = '';
                if (candidate.match_results && candidate.match_results.length > 0) {
                    candidate.match_results.forEach(mr => {
                        // `suggestions` được lưu là JSON string, cần parse lại
                        const suggestions = JSON.parse(mr.suggestions || "[]").map(s => `<li>${s}</li>`).join('');
                        matchResultsDiv.innerHTML += `
                            <p><strong>Ngày:</strong> ${new Date(mr.created_at).toLocaleString()}</p>
                            <p><strong>Điểm phù hợp:</strong> ${mr.match_score}%</p>
                            <p><strong>Phản hồi:</strong> ${mr.feedback}</p>
                            <p><strong>Gợi ý:</strong></p><ul>${suggestions}</ul><hr>
                        `;
                    });
                } else {
                    matchResultsDiv.textContent = 'Chưa có kết quả phân tích CV/JD.';
                }

                // Tải và hiển thị Kết quả phỏng vấn AI
                const interviewResultsDiv = document.getElementById('detail-interview-results');
                interviewResultsDiv.innerHTML = '';
                if (candidate.interviews && candidate.interviews.length > 0) {
                    candidate.interviews.forEach(iv => {
                        interviewResultsDiv.innerHTML += `
                            <p><strong>Phiên ID:</strong> ${iv.session_id}</p>
                            <p><strong>Bắt đầu:</strong> ${new Date(iv.start_time).toLocaleString()}</p>
                            <p><strong>Kết thúc:</strong> ${iv.end_time ? new Date(iv.end_time).toLocaleString() : 'Đang diễn ra'}</p>
                            <p><strong>Điểm tổng quan:</strong> ${iv.overall_score || 'N/A'}</p>
                            <p><strong>Phản hồi tổng quan:</strong> ${iv.overall_feedback || 'N/A'}</p><hr>
                        `;
                    });
                } else {
                    interviewResultsDiv.textContent = 'Chưa có kết quả phỏng vấn AI.';
                }

                // Tải và hiển thị Kết quả kiểm tra kỹ năng
                const skillTestResultsDiv = document.getElementById('detail-skill-test-results');
    skillTestResultsDiv.innerHTML = '';
    if (candidate.skill_tests && candidate.skill_tests.length > 0) {
        // Duyệt qua từng bài kiểm tra và lấy chi tiết từng câu trả lời
        for (const st of candidate.skill_tests) {
            // Cần gọi API riêng để lấy chi tiết của một bài test theo test_id
            // Vì quan hệ items của SkillTestResult không được tự động tải trong CandidatePublic
            const detailedTestResult = await fetchData(`/api/tests/results/${st.id}`);
            let itemsHtml = '';
            detailedTestResult.items.forEach(item => {
                itemsHtml += `
                    <li><strong>${item.question_text}</strong>: ${item.selected_answer || 'Không trả lời'} (<span style="color: ${item.is_correct ? 'green' : 'red'};">${item.is_correct ? 'Đúng' : 'Sai'}</span>)</li>
                `;
            });
            skillTestResultsDiv.innerHTML += `
                <p><strong>Bài kiểm tra ID:</strong> ${st.id}</p>
                <p><strong>Bắt đầu:</strong> ${new Date(st.start_time).toLocaleString()}</p>
                <p><strong>Kết thúc:</strong> ${st.end_time ? new Date(st.end_time).toLocaleString() : 'Đang diễn ra'}</p>
                <p><strong>Điểm:</strong> ${st.score || 'N/A'} / ${st.total_questions || 'N/A'}</p>
                <p><strong>Chi tiết:</strong></p><ul>${itemsHtml}</ul><hr>
            `;
        }
    } else {
        skillTestResultsDiv.textContent = 'Chưa có kết quả kiểm tra kỹ năng.';
    }


                candidateDetailsDiv.style.display = 'block'; // Hiển thị chi tiết ứng viên
            } catch (error) {
                alert('Lỗi khi tải chi tiết ứng viên: ' + error.message);
                console.error('Candidate details error:', error);
            }
        }
    });

    // --- Gửi thư mời ---
    sendOfferButton.addEventListener('click', async () => {
        if (!selectedCandidateForOffer) {
            alert('Vui lòng chọn một ứng viên để gửi thư mời.');
            return;
        }
        if (!confirm('Bạn có chắc chắn muốn gửi thư mời làm việc đến ứng viên này không?')) {
            return;
        }

        try {
            // Lấy thông tin ứng viên để có email và tên
            const candidate = await fetchData(`/api/candidates/${selectedCandidateForOffer}`);
            await fetchData('/api/candidates/send-offer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate_id: parseInt(selectedCandidateForOffer),
                    recipient_email: candidate.email,
                    candidate_name: candidate.full_name,
                    position_name: candidate.applied_position || 'Vị trí đã ứng tuyển'
                })
            });
            alert('Thư mời đã được gửi thành công!');
        } catch (error) {
            alert('Lỗi khi gửi thư mời: ' + error.message);
            console.error('Send offer error:', error);
        }
    });


    // --- Khởi tạo ban đầu ---
    checkAuth(); // Kiểm tra trạng thái đăng nhập khi tải trang
    if (getToken()) {
        loadCandidates(); // Tải danh sách ứng viên nếu đã đăng nhập
    }
});