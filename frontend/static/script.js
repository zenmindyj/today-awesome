document.addEventListener('DOMContentLoaded', function() {
    // This script is now simplified as it doesn't need to handle different modes dynamically.
    // The mode is determined by which HTML file is loaded (index.html for user, demo.html for demo).

    const pageMode = document.body.dataset.mode; // 'user' or 'demo'
    const apiPrefix = pageMode === 'user' ? '/api/user' : '/api/demo';

    // --- Element Selection ---
    const entryForm = document.getElementById('entryForm');
    const entriesList = document.getElementById('entriesList');
    const generateSummaryBtn = document.getElementById('generateSummary');
    const summaryContent = document.getElementById('summaryContent');
    const timeRangeSelect = document.getElementById('timeRangeSelect');
    const customDateRange = document.getElementById('customDateRange');
    const summaryStartDate = document.getElementById('summaryStartDate');
    const summaryEndDate = document.getElementById('summaryEndDate');
    const textImportInput = document.getElementById('textImportInput');
    const textImportBtn = document.getElementById('textImportBtn');
    const queryInput = document.getElementById('queryInput');
    const askQuestionBtn = document.getElementById('askQuestion');
    const queryResult = document.getElementById('queryResult');
    const answer = document.getElementById('answer');

    // --- Core Functions ---

    // Load summary time range options
    async function loadSummaryOptions() {
        try {
            const response = await fetch(`${apiPrefix}/summary-options`);
            if (!response.ok) throw new Error('Failed to fetch summary options');
            
            const data = await response.json();
            timeRangeSelect.innerHTML = ''; // Clear existing options
            
            data.week_options.forEach(option => {
                const opt = document.createElement('option');
                opt.value = `week_${option.start_date}_${option.end_date}`;
                opt.textContent = option.name;
                timeRangeSelect.appendChild(opt);
            });
            
            data.month_options.forEach(option => {
                const opt = document.createElement('option');
                opt.value = `month_${option.start_date}_${option.end_date}`;
                opt.textContent = option.name;
                timeRangeSelect.appendChild(opt);
            });
            
            const customOpt = document.createElement('option');
            customOpt.value = 'custom';
            customOpt.textContent = '自定义时间';
            timeRangeSelect.appendChild(customOpt);
        } catch (error) {
            console.error('加载总结选项失败:', error);
            showMessage('加载总结时间范围失败', 'error');
        }
    }

    // Load and display entries with pagination
    let currentPage = 1;
    const entriesPerPage = 25;
    let totalPages = 1;

    window.loadEntries = async function(page = 1) {
        try {
            const response = await fetch(`${apiPrefix}/entries?page=${page}&per_page=${entriesPerPage}`);
            const data = await response.json();
            
            if (response.ok) {
                currentPage = data.pagination.current_page;
                totalPages = data.pagination.total_pages;
                displayEntries(data.entries);
                updatePaginationControls();
            }
        } catch (error) {
            console.error('加载条目失败:', error);
        }
    }

    // Display entries in the list
    function displayEntries(entries) {
        if (entries.length === 0) {
            const message = pageMode === 'user' ? '还没有记录任何好棒的时刻，开始记录吧！' : '没有可供演示的记录。';
            entriesList.innerHTML = `<p>${message}</p>`;
            return;
        }
        
        entriesList.innerHTML = entries.map(entry => `
            <div class="entry-item" data-entry-id="${entry[0]}">
                <div class="entry-content">${entry[1]}</div>
                <div class="entry-meta">
                    <div>
                        ${entry[6] ? `编码: ${entry[6]} | ` : ''}
                        ${entry[2] ? `分类: ${entry[2]} | ` : ''}
                        时间: ${entry[5] || (entry[3] ? new Date(entry[3]).toISOString().split('T')[0] : '')}
                    </div>
                    <button class="delete-btn" onclick="deleteEntry(${entry[0]})" title="删除记录">×</button>
                </div>
            </div>
        `).join('');
    }
    
    // Update pagination controls
    function updatePaginationControls() {
        const paginationContainer = document.getElementById('paginationContainer');
        if (!paginationContainer || totalPages <= 1) {
            if (paginationContainer) paginationContainer.innerHTML = '';
            return;
        }
        
        let paginationHTML = '<div class="pagination">';
        if (currentPage > 1) paginationHTML += `<button class="page-btn" onclick="window.loadEntries(${currentPage - 1})">上一页</button>`;
        
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        if (startPage > 1) {
            paginationHTML += `<button class="page-btn" onclick="window.loadEntries(1)">1</button>`;
            if (startPage > 2) paginationHTML += '<span class="page-ellipsis">...</span>';
        }
        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="window.loadEntries(${i})">${i}</button>`;
        }
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) paginationHTML += '<span class="page-ellipsis">...</span>';
            paginationHTML += `<button class="page-btn" onclick="window.loadEntries(${totalPages})">${totalPages}</button>`;
        }
        if (currentPage < totalPages) paginationHTML += `<button class="page-btn" onclick="window.loadEntries(${currentPage + 1})">下一页</button>`;
        
        paginationHTML += '</div>';
        paginationContainer.innerHTML = paginationHTML;
    }

    // Delete an entry (only available in user mode)
    window.deleteEntry = async function(entryId) {
        if (!confirm('确定要删除这条记录吗？此操作无法撤销。')) return;
        
        try {
            const response = await fetch(`${apiPrefix}/entries/${entryId}`, { method: 'DELETE' });
            if (response.ok) {
                showMessage('记录删除成功', 'success');
                window.loadEntries(currentPage);
            } else {
                const data = await response.json();
                throw new Error(data.detail || '删除失败');
            }
        } catch (error) {
            showMessage(`删除失败：${error.message}`, 'error');
        }
    }

    // Show a temporary message
    function showMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        document.body.appendChild(messageDiv);
        setTimeout(() => messageDiv.remove(), 3000);
    }


    // --- Event Listeners ---

    // Add single entry
    entryForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const contentInput = document.getElementById('content');
        const content = contentInput.value.trim();
        if (!content) return;

        if (pageMode === 'demo') {
            // Sandbox mode: add to frontend only
            const tempEntryHTML = `
                <div class="entry-item" data-entry-id="temp_${new Date().getTime()}">
                    <div class="entry-content">${content.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
                    <div class="entry-meta">
                        <div>
                            <span class="temp-entry-tag">临时</span>
                            分类: AI 自动分类 | 
                            时间: ${new Date().toISOString().split('T')[0]}
                        </div>
                    </div>
                </div>`;
            
            // If the list is showing the "empty" message, replace it
            const emptyMessage = entriesList.querySelector('p');
            if (emptyMessage) {
                entriesList.innerHTML = tempEntryHTML;
            } else {
                entriesList.insertAdjacentHTML('afterbegin', tempEntryHTML);
            }
            
            contentInput.value = '';
            showMessage('提示: 演示模式下添加的记录是临时的，刷新后会消失。', 'info');
            return;
        }

        // User mode: send to backend
        try {
            const response = await fetch(`${apiPrefix}/entries`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });
            if (response.ok) {
                contentInput.value = '';
                window.loadEntries();
                showMessage('条目添加成功！AI正在为您自动分类...', 'success');
            } else {
                throw new Error('添加失败');
            }
        } catch (error) {
            showMessage('添加失败，请重试', 'error');
        }
    });

    // Batch import text records
    textImportBtn.addEventListener('click', async function() {
        const textContent = textImportInput.value.trim();
        if (!textContent) {
            showMessage('请输入要导入的记录', 'error');
            return;
        }
        
        const lines = textContent.split('\n').filter(line => line.trim());
        const entries = lines.map(line => {
            const parts = line.split(' | ');
            if (parts.length === 2 && parts[0].match(/\d{4}[-/]\d{1,2}[-/]\d{1,2}/)) {
                return { content: parts[1].trim(), entry_date: parts[0].trim().replace(/\//g, '-') };
            } else if (parts.length === 2 && parts[1].match(/\d{4}[-/]\d{1,2}[-/]\d{1,2}/)) {
                return { content: parts[0].trim(), entry_date: parts[1].trim().replace(/\//g, '-') };
            }
            return { content: line.trim(), entry_date: null };
        }).filter(e => e.content);
        
        if (entries.length === 0) {
            showMessage('没有找到有效的记录', 'error');
            return;
        }

        if (pageMode === 'demo') {
            // Sandbox mode: add to frontend only
            let tempEntriesHTML = '';
            for (const entry of entries) {
                tempEntriesHTML += `
                    <div class="entry-item" data-entry-id="temp_${new Date().getTime()}">
                        <div class="entry-content">${entry.content.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
                        <div class="entry-meta">
                            <div>
                                <span class="temp-entry-tag">临时</span>
                                分类: AI 自动分类 | 
                                时间: ${entry.entry_date || new Date().toISOString().split('T')[0]}
                            </div>
                        </div>
                    </div>`;
            }

            const emptyMessage = entriesList.querySelector('p');
            if (emptyMessage) {
                entriesList.innerHTML = tempEntriesHTML;
            } else {
                entriesList.insertAdjacentHTML('afterbegin', tempEntriesHTML);
            }
            
            textImportInput.value = '';
            showMessage('提示: 演示模式下添加的记录是临时的，刷新后会消失。', 'info');
            return;
        }

        // User mode: send to backend
        textImportBtn.disabled = true;
        textImportBtn.textContent = '正在导入...';
        try {
            const response = await fetch(`${apiPrefix}/import-text`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ entries })
            });
            const data = await response.json();
            if (response.ok) {
                showMessage(`成功导入 ${data.success_count} 条记录`, 'success');
                textImportInput.value = '';
                loadEntries();
            } else {
                throw new Error(data.detail || '导入失败');
            }
        } catch (error) {
            showMessage('导入失败：' + error.message, 'error');
        } finally {
            textImportBtn.disabled = false;
            textImportBtn.textContent = '批量添加文本记录';
        }
    });

    // COMMON event listeners for both modes
    timeRangeSelect.addEventListener('change', function() {
        customDateRange.style.display = this.value === 'custom' ? 'block' : 'none';
    });

    generateSummaryBtn.addEventListener('click', async function() {
        let requestData = {};
        if (timeRangeSelect.value === 'custom') {
            if (!summaryStartDate.value || !summaryEndDate.value) {
                alert('请选择开始和结束日期');
                return;
            }
            requestData = { start_date: summaryStartDate.value, end_date: summaryEndDate.value };
        } else {
            const parts = timeRangeSelect.value.split('_');
            requestData = { start_date: parts[1], end_date: parts[2] };
        }
        
        summaryContent.innerHTML = '<div class="loading">AI 正在生成总结...</div>';
        generateSummaryBtn.disabled = true;
        
        try {
            const response = await fetch(`${apiPrefix}/summary`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            const data = await response.json();
            if (response.ok) {
                const renderedSummary = marked.parse(data.summary);
                summaryContent.innerHTML = `
                    <div class="summary">
                        <h3>AI 总结</h3>
                        <div class="markdown-content">${renderedSummary}</div>
                        <p class="summary-meta">基于 ${data.entries_count} 条记录生成</p>
                    </div>
                `;
            } else {
                throw new Error(data.detail || '生成总结失败');
            }
        } catch (error) {
            summaryContent.innerHTML = `<div class="error">生成总结失败：${error.message}</div>`;
        } finally {
            generateSummaryBtn.disabled = false;
        }
    });

    askQuestionBtn.addEventListener('click', async function() {
        const question = queryInput.value.trim();
        if (!question) {
            showMessage('请输入您的问题', 'error');
            return;
        }
        
        answer.innerHTML = '<div class="loading">AI 正在思考您的问题...</div>';
        askQuestionBtn.disabled = true;
        
        try {
            const response = await fetch(`${apiPrefix}/smart-query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            const data = await response.json();
            
            if (response.ok) {
                let rawEntriesHtml = '';
                if (data.relevant_entries && data.relevant_entries.length > 0) {
                    rawEntriesHtml = `
                        <div class="raw-entries-section">
                            <h3>相关原始条目：</h3>
                            <div class="raw-entries-list">
                                ${data.relevant_entries.map(entry => `
                                    <div class="raw-entry-item">
                                        <span class="raw-entry-date">${entry[5] || (entry[3] ? new Date(entry[3]).toISOString().split('T')[0] : '')}</span>
                                        <span class="raw-entry-content">${entry[1] || ''}</span>
                                    </div>
                                `).join('')}
                            </div>
                            <p class="raw-entries-note">显示 ${data.relevant_entries.length} 条相关记录</p>
                        </div>
                    `;
                }
                const renderedAnswer = marked.parse(data.answer);
                answer.innerHTML = rawEntriesHtml + `
                    <div class="ai-answer-section">
                        <h3>AI分析回答：</h3>
                        <div class="answer-content markdown-content">${renderedAnswer}</div>
                    </div>
                `;
            } else {
                throw new Error(data.detail || '查询失败');
            }
        } catch (error) {
            answer.innerHTML = `<div class="error">查询失败：${error.message}</div>`;
        } finally {
            askQuestionBtn.disabled = false;
        }
    });

    queryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') askQuestionBtn.click();
    });


    // --- Initial Page Load ---
    loadSummaryOptions();
    window.loadEntries();
});
