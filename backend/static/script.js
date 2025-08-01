let editingId = null;
let allTransactions = [];
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("transactionForm");
    const table = document.querySelector("#transactionsTable tbody");
    const themeToggle = document.getElementById("themeToggle");
    

    // Load theme
    if (localStorage.getItem("darkMode") === "true") {
        document.body.classList.add("dark");
    }

    themeToggle.addEventListener("click", () => {
        document.body.classList.toggle("dark");
        localStorage.setItem("darkMode", document.body.classList.contains("dark"));
    });

    function formatToIST(timestamp) {
    if (!timestamp) return "Unavailable";

    // Fix timestamp format: convert "YYYY-MM-DD HH:MM:SS" to "YYYY-MM-DDTHH:MM:SS"
    const isoString = timestamp.replace(" ", "T");

    const date = new Date(isoString);
    if (isNaN(date)) return "Invalid";

    return date.toLocaleString("en-IN", {
        timeZone: "Asia/Kolkata",
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true
    });
}




    function formatDateToIST(dateStr) {
        const date = new Date(dateStr);
        if (isNaN(date)) return "Invalid";

        return date.toLocaleDateString("en-IN", {
            timeZone: "Asia/Kolkata",
            year: "numeric",
            month: "short",
            day: "numeric"
        });
    }

    function renderTransactions(transactions) {
        table.innerHTML = "";
        transactions.forEach((tx) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${tx.amount}</td>
                <td>${tx.type}</td>
                <td>${tx.category}</td>
                <td>${formatDateToIST(tx.date)}</td>
                <td>${tx.note || ""}</td>
                <td>${formatToIST(tx.timestamp)}</td>
                <td>
                    <button onclick='editTransaction(${JSON.stringify(tx)})'>Edit</button>
                    <button onclick='deleteTransaction(${tx.id})'>Delete</button>
                </td>
            `;
            table.appendChild(row);
        });
    }
    function applyFilters(transactions) {
        const dateFilter = document.getElementById("filterDate").value;
        const monthFilter = document.getElementById("filterMonth").value;
        const yearFilter = document.getElementById("filterYear").value;
        const categoryFilter = document.getElementById("filterCategory").value.toLowerCase();

        return transactions.filter(tx => {
            const txDate = new Date(tx.date);
            const txDay = txDate.toISOString().split("T")[0]; // e.g. "2025-07-23"
            const txMonth = txDate.getMonth() + 1; // getMonth() is 0-based
            const txYear = txDate.getFullYear();
            const matchDate = !dateFilter || txDay === dateFilter;
            const matchMonth = !monthFilter || txMonth === parseInt(monthFilter);
            const matchYear = !yearFilter || txYear === parseInt(yearFilter);
            const matchCategory = !categoryFilter || tx.category.toLowerCase().includes(categoryFilter);
            return matchDate && matchMonth && matchYear && matchCategory;
        });
    }



    function loadTransactions() {
        fetch("/transactions")
            .then((res) => res.json())
            .then((data) => {
                table.innerHTML = "";
                allTransactions = data;
                renderTransactions(data);

            });
    }
    document.getElementById("applyFilters").addEventListener("click", () => {
        const filtered = applyFilters(allTransactions);
        renderTransactions(filtered);
    });

    document.getElementById("clearFilters").addEventListener("click", () => {
        document.getElementById("filterDate").value = "";
        document.getElementById("filterMonth").value = "";
        document.getElementById("filterYear").value = "";
        document.getElementById("filterCategory").value = "";
        renderTransactions(allTransactions);
    });



    window.deleteTransaction=function(id) {
        const confirmDelete = confirm("Are you sure you want to delete this transaction?");
        if (!confirmDelete) return;

        fetch(`/transactions/${id}`, {
            method: 'DELETE'
        }).then(res => res.json())
        .then(data => {
            if (data.success) {
                loadTransactions(); // Reload table
            } else {
                alert("Failed to delete");
            }
        });
    }

    window.editTransaction=function(tx) {
        document.getElementById("amount").value = tx.amount;
        document.getElementById("type").value = tx.type;
        document.getElementById("category").value = tx.category;
        document.getElementById("date").value = tx.date.split("T")[0];
        document.getElementById("note").value = tx.note || "";
        editingId = tx.id;
        form.setAttribute("data-id", tx.id);
    }

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        const formData = {
            amount: parseFloat(form.amount.value),
            type: form.type.value,
            category: form.category.value,
            date: form.date.value,
            note: form.note.value
        };

        const id = form.getAttribute("data-id");

        fetch("/transactions", {
            method: id ? "PUT" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...formData, id }),
        }).then(() => {
            form.reset();
            form.removeAttribute("data-id");
            loadTransactions();
        });
    });

    loadTransactions();
});
