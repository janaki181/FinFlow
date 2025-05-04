document.getElementById("add-btn").addEventListener("click", async () => {
    const title = document.getElementById("task-input").value;
    const priority = document.getElementById("priority-input").value;
    console.log("Task:", title, "Priority:", priority);
    
    if (!title) {
        alert("Financial goal cannot be empty!");
        return;
    }
    
    const taskData = { title, priority };
    
    try {
        await addTask(taskData);
        // Clear the input fields after adding
        document.getElementById("task-input").value = "";
        document.getElementById("priority-input").value = "";
        // Load the tasks to display the newly added one
        loadTasks();
    } catch (error) {
        console.error("Failed to add task:", error);
        alert("Failed to add your financial goal. Please try again.");
    }
});

// Event listener for the view goals button
document.getElementById("view-btn").addEventListener("click", () => {
    loadTasks();
});

async function addTask(taskData) {
    try {
        const response = await fetch('/add-task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log("Financial goal added successfully:", data);
        } else {
            console.error("Error adding financial goal:", data.error);
            throw new Error(data.error);
        }
    } catch (error) {
        console.error("Request failed", error);
        throw error;
    }
}

async function loadTasks() {
    try {
        console.log("Fetching tasks...");
        const response = await fetch('/get-tasks');
        
        const data = await response.json();
        
        if (response.ok) {
            console.log("Tasks fetched successfully:", data);
            const taskContainer = document.getElementById("taskContainer");
            
            // Clear existing tasks
            taskContainer.innerHTML = '';
            
            if (data.length === 0) {
                taskContainer.innerHTML = '<p class="no-tasks">No financial goals found. Add some goals to get started!</p>';
                return;
            }
            
            // Map timeframe values to readable text
            const timeframes = {
                "1": "1 Month",
                "2": "3 Months",
                "3": "6 Months",
                "4": "1 Year",
                "5": "5+ Years"
            };
            
            // Add tasks to the container
            data.forEach(task => {
                const taskElement = document.createElement('div');
                taskElement.className = 'task-item';
                
                const timeframeText = timeframes[task.priority] || "Unknown timeframe";
                
                taskElement.innerHTML = `
                    <div class="task-content">
                        <h3>${task.title}</h3>
                        <p>Timeframe: ${timeframeText}</p>
                    </div>
                    <div class="task-actions">
                        <button class="delete-btn" data-id="${task._id}">Delete</button>
                    </div>
                `;
                
                taskContainer.appendChild(taskElement);
            });
            
            // Add event listeners to delete buttons
            document.querySelectorAll('.delete-btn').forEach(button => {
                button.addEventListener('click', async (e) => {
                    const taskId = e.target.getAttribute('data-id');
                    await deleteTask(taskId);
                });
            });
            
        } else {
            console.error("Error fetching tasks:", data.error);
            throw new Error(data.error);
        }
    } catch (error) {
        console.error("Request failed", error);
        const taskContainer = document.getElementById("taskContainer");
        taskContainer.innerHTML = '<p class="error">Failed to load financial goals. Please try again later.</p>';
    }
}

async function deleteTask(taskId) {
    try {
        console.log("Deleting task:", taskId);
        const response = await fetch(`/delete-task/${taskId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log("Financial goal deleted successfully:", data);
            loadTasks(); // Reload tasks after deletion
        } else {
            console.error("Error deleting financial goal:", data.error);
            alert("Failed to delete financial goal. Please try again.");
        }
    } catch (error) {
        console.error("Request failed", error);
        alert("Failed to delete financial goal. Please try again.");
    }
}

// Load tasks when the page loads
document.addEventListener("DOMContentLoaded", () => {
    loadTasks();
});