document.addEventListener('DOMContentLoaded', function () {
    
    // DOM Elements
    const themeToggle = document.getElementById('theme-toggle');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const studentForm = document.getElementById('student-form');
    const facultyForm = document.getElementById('faculty-form');
    const studentInput = document.getElementById('student-input');
    const facultyInput = document.getElementById('faculty-input');
    const studentResults = document.getElementById('student-results');
    const facultyResults = document.getElementById('faculty-results');
    const studentNoResults = document.getElementById('student-no-results');
    const facultyNoResults = document.getElementById('faculty-no-results');
    const studentTableBody = document.getElementById('student-table-body');
    const facultyTableBody = document.getElementById('faculty-table-body');
    const studentSearchTerm = document.getElementById('student-search-term');
    const facultySearchTerm = document.getElementById('faculty-search-term');
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    const loading = document.getElementById('loading');

    // Theme Toggle
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        document.body.classList.toggle('light-mode');

        // Save theme preference
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
    });

    // Apply saved theme
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.remove('light-mode');
        document.body.classList.add('dark-mode');
    }

    // Tab Navigation
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // Update active button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // Show corresponding content
            tabContents.forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });

    // Form Submission Handlers
    studentForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const rollNo = studentInput.value.trim().toUpperCase();

        if (!rollNo) return;

        // Show loading
        showLoading();

        //fetch
        fetch(`/student/${rollNo}`)
            .then(async response => {
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Unknown error');
                }
                return response.json();
            })
            .then(data => data.map((item) => ({
                rollNo: item['rollno'], 
                examDay: item['day'], 
                courseCode: item['coursecode'], 
                date: item['date'], 
                shift: item['shift'], 
                roomNo: item['roomno'],
                courseName: item['coursename'] || '-'
            })))
            .then((data) => {
                console.log(data);
                studentSearchTerm.textContent = rollNo;
                renderStudentResults(data);
                studentResults.style.display = 'block';
                studentNoResults.style.display = 'none';
            }).catch((error) => {
                studentSearchTerm.textContent = rollNo;
                renderStudentResults([]);
                studentResults.style.display = 'none';
                studentNoResults.style.display = 'block';
                console.error(`Error: ${error.message}`);
                showToast(`Error: ${error.message}`, true);
            }).finally(() => {
                hideLoading();
            })
    });

    facultyForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const courseCode = facultyInput.value.trim().toUpperCase();

        if (!courseCode) return;

        // Show loading
        showLoading();

        fetch(`/faculty/${courseCode}`)
            .then(async response => {
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Unknown error');
                }
                return response.json();
            })
            .then(data => {
                const courseCode = data['coursecode'];
                const day = data['day'];
                const shift = data['shift'];
                const date = data['date'];
                const coursename = data['coursename'] || '-'
                return data['roomno'].map((roomno) => ({
                    courseCode, day, shift, date, 
                    roomNos: roomno,
                    courseName: coursename
                }))
            })
            .then((data) => {
                console.log(data);
                facultySearchTerm.textContent = courseCode;
                renderFacultyResults(data);
                facultyResults.style.display = 'block';
                facultyNoResults.style.display = 'none';
            }).catch((error) => {
                facultySearchTerm.textContent = courseCode;
                renderFacultyResults([]);
                facultyResults.style.display = 'none';
                facultyNoResults.style.display = 'block';
                console.error(`Error: ${error.message}`);
                showToast(`Error: ${error.message}`, true);
            }).finally(() => {
                hideLoading();
            })

    });

    // Render Results Functions
    function renderStudentResults(data) {
        studentTableBody.innerHTML = '';

        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
          <td>${item.rollNo}</td>
          <td>${item.examDay}</td>
          <td>${item.courseCode}</td>
          <td>${item.date}</td>
          <td>${item.shift}</td>
          <td>${item.roomNo}</td>
          <td>${item.courseName}</td>
        `;
            studentTableBody.appendChild(row);
        });
    }

    function renderFacultyResults(data) {
        facultyTableBody.innerHTML = '';

        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
          <td>${item.courseCode}</td>
          <td>${item.day}</td>
          <td>${item.shift}</td>
          <td>${item.date}</td>
          <td>${item.roomNos}</td>
          <td>${item.courseName}</td>
        `;
            facultyTableBody.appendChild(row);
        });
    }

    // Toast Function
    function showToast(message, isError = false) {
        toastMessage.textContent = message;
   
        if (isError) toast.classList.add('error');
        else toast.classList.remove('error');

        toast.classList.add('show');

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // Loading Overlay Functions
    function showLoading() {
        loading.classList.add('show');
    }

    function hideLoading() {
        loading.classList.remove('show');
    }

    // Mobile Responsiveness - Adjust tab text based on screen size
    function updateTabText() {
        const isMobile = window.innerWidth < 640;
        const tabElements = document.querySelectorAll('.tab-text');

        tabElements.forEach(tab => {
            if (isMobile) {
                if (tab.textContent === 'Student Search') tab.textContent = 'Student';
                if (tab.textContent === 'Faculty Search') tab.textContent = 'Faculty';
            } else {
                if (tab.textContent === 'Student') tab.textContent = 'Student Search';
                if (tab.textContent === 'Faculty') tab.textContent = 'Faculty Search';
            }
        });
    }

    // Initial call and event listener for resize
    updateTabText();
    window.addEventListener('resize', updateTabText);
});
