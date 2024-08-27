document.addEventListener('DOMContentLoaded', function () {
    const taskSections = document.querySelectorAll('.task-section');

    taskSections.forEach(section => {
        section.addEventListener('transitionend', function () {
            this.classList.add('task-moved');
        });
    });

    document.querySelectorAll('.task-actions a').forEach(button => {
        button.addEventListener('click', function () {
            const taskItem = this.closest('.list-group-item');
            taskItem.classList.add('move-task');
            setTimeout(() => {
                taskItem.classList.remove('move-task');
            }, 300); // Animasyon süresi ile eşleşmeli
        });
    });
});
