from django.db import models
from django.db.models import Count, Q
from django.contrib.auth.models import User


class Project(models.Model):
    """Top-level container that groups sprints and backlog items."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner_id = models.IntegerField(
        help_text="References auth.User.id in the auth database"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def owner(self):
        """Resolve the owner User from the auth database."""
        from django.contrib.auth.models import User
        try:
            return User.objects.using('default').get(pk=self.owner_id)
        except User.DoesNotExist:
            return None

    @property
    def active_sprint(self):
        return self.sprints.filter(status=Sprint.Status.ACTIVE).first()

    @property
    def item_counts(self):
        """Status breakdown: {status_value: count, ..., 'total': N}."""
        qs = self.backlog_items.values('status').annotate(n=Count('id'))
        counts = {row['status']: row['n'] for row in qs}
        counts['total'] = sum(counts.values())
        return counts

    @property
    def completion_percentage(self):
        """Percentage of all project items that have reached Complete."""
        counts = self.item_counts
        total = counts.get('total', 0)
        if total == 0:
            return 0
        return round(counts.get('DONE', 0) / total * 100, 1)

    collaborators = models.ManyToManyField(
        User, 
        related_name='shared_projects', 
        blank=True,
        help_text="Users invited to work on this project"
    )


class Sprint(models.Model):
    """A time-boxed iteration within a project."""

    class Status(models.TextChoices):
        PLANNING = 'PLANNING', 'Planning'
        ACTIVE = 'ACTIVE', 'Active'
        CLOSED = 'CLOSED', 'Closed'

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='sprints'
    )
    name = models.CharField(max_length=100)
    goal = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PLANNING,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} — {self.name}"

    @property
    def item_counts(self):
        """Status breakdown for items assigned to this sprint."""
        qs = self.items.values('status').annotate(n=Count('id'))
        counts = {row['status']: row['n'] for row in qs}
        counts['total'] = sum(counts.values())
        return counts

    @property
    def completion_percentage(self):
        """Percentage of sprint items that have reached Complete."""
        counts = self.item_counts
        total = counts.get('total', 0)
        if total == 0:
            return 0
        return round(counts.get('DONE', 0) / total * 100, 1)


class BacklogItem(models.Model):
    """
    A work item that flows through the Agile board.

    Lifecycle:
        Product Backlog  ──►  Sprint Backlog  ──►  Ready for Test
                                    ▲                    │
                                    │       ┌────────────┤
                                    │       ▼            ▼
                                  (fail)           Complete
                                rework in          (ready for
                                 sprint             release)
    """

    class Status(models.TextChoices):
        PRODUCT_BACKLOG = 'BACKLOG', 'Product Backlog'
        SPRINT_BACKLOG = 'SPRINT', 'Sprint Backlog'
        READY_FOR_TEST = 'TEST', 'Ready for Test'
        COMPLETE = 'DONE', 'Complete'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MED', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRIT', 'Critical'

    VALID_TRANSITIONS = {
        'BACKLOG': ['SPRINT'],
        'SPRINT': ['TEST', 'BACKLOG'],
        'TEST': ['DONE', 'SPRINT'],   # DONE = pass, SPRINT = fail/rework
        'DONE': ['BACKLOG'],           # re-open if needed
    }

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='backlog_items'
    )
    sprint = models.ForeignKey(
        Sprint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PRODUCT_BACKLOG,
    )
    priority = models.CharField(
        max_length=5,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    assigned_to_id = models.IntegerField(
        null=True, blank=True,
        help_text="References auth.User.id in the auth database",
    )
    created_by_id = models.IntegerField(
        help_text="References auth.User.id in the auth database"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-updated_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def can_transition_to(self, new_status):
        """Return True if the workflow allows moving to *new_status*."""
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    @property
    def assigned_to(self):
        """Resolve the assigned User from the auth database."""
        if not self.assigned_to_id:
            return None
        from django.contrib.auth.models import User
        try:
            return User.objects.using('default').get(pk=self.assigned_to_id)
        except User.DoesNotExist:
            return None

    @property
    def created_by(self):
        """Resolve the creator User from the auth database."""
        from django.contrib.auth.models import User
        try:
            return User.objects.using('default').get(pk=self.created_by_id)
        except User.DoesNotExist:
            return None


class StageComment(models.Model):
    """Tracks comments left when an item transitions between stages."""
    
    item = models.ForeignKey(
        BacklogItem, 
        on_delete=models.CASCADE, 
        related_name='transition_comments'
    )
    author_id = models.IntegerField(
        help_text="References auth.User.id in the auth database"
    )
    
    # Track exactly where it moved from and to
    from_stage = models.CharField(max_length=10, choices=BacklogItem.Status.choices)
    to_stage = models.CharField(max_length=10, choices=BacklogItem.Status.choices)
    
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # Shows newest comments first

    @property
    def author(self):
        """Resolve the author User from the auth database."""
        from django.contrib.auth.models import User
        try:
            return User.objects.using('default').get(pk=self.author_id)
        except User.DoesNotExist:
            return None