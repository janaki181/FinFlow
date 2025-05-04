document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('taskForm');
    const viewBtn = document.getElementById('view-btn');
    const taskContainer = document.getElementById('taskContainer');

    // Add goal
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const title = document.getElementById('task-input').value;
        const timeframe = document.getElementById('priority-input').value;

        if (!title || !timeframe) {
            alert("Please enter both title and timeframe");
            return;
        }

        const response = await fetch('/add-goal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, timeframe })
        });

        if (response.ok) {
            document.getElementById('task-input').value = '';
            document.getElementById('priority-input').value = '';
            loadGoals(); // Refresh the list
        } else {
            alert("Failed to add goal");
        }
    });

    // View goals
    viewBtn.addEventListener('click', loadGoals);

    async function loadGoals() {
        const response = await fetch('/get-goals');
        const data = await response.json();
        
        taskContainer.innerHTML = ''; // Clear existing

        if (data.length === 0) {
            taskContainer.innerHTML = '<p>No goals added yet.</p>';
            return;
        }

        data.forEach(goal => {
            const goalDiv = document.createElement('div');
            goalDiv.className = 'goal';
            goalDiv.innerHTML = `
                <h3>${goal.title}</h3>
                <p>Timeframe: ${convertTimeframe(goal.timeframe)}</p>
                <p>Created: ${new Date(goal.created_at).toLocaleDateString()}</p>
            `;
            taskContainer.appendChild(goalDiv);
        });
    }

    function convertTimeframe(code) {
        const map = {
            1: "1 Month",
            2: "3 Months",
            3: "6 Months",
            4: "1 Year",
            5: "5+ Years"
        };
        return map[code] || "Unknown";
    }
});
