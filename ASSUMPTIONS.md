# Decisions and assumptions

- The linked TaskBoard repository is the reference assignment, not the final submission. Its assignment files and history are retained for attribution.
- The user selected helpdesk ticket management. ResolveDesk implements requester email, priorities, assignment, status queues, search and ticket lifecycle operations.
- This is an internal classroom demonstration. Only synthetic tickets are used. Authentication, external email delivery and public production access are outside the requested minimum scope.
- The user authorized temporary AWS provisioning and teardown in the account selected during AWS login. Region ap-south-1 follows the reference assignment.
- The same temporary EKS cluster is shared with Aryan’s CampusDesk demonstration. Separate namespaces, database Secrets and persistent volumes isolate the two applications. Cloud infrastructure evidence is explicitly shared.
- CampusDesk adds campus request categories and required location fields. It is a declared derivative, not an assertion of independent authorship. Both students should understand and present their work; assessment of originality remains with the instructor.
- Each GitHub account was authenticated separately. Commits retain the actual configured operator identity; no student authorship is fabricated.
- Browser screenshots and test output document actual runs. Slide/video explanations are generated aids. Missing evidence is reported instead of simulated.
- Database migrations are a single job per deployed image revision. Application replicas wait for the expected revision before serving traffic.
- CI publishes immutable SHA-tagged images after tests, strict vulnerability scans and a temporary Kubernetes deployment. GitOps promotes a selected tested SHA through a separate values change.
- All temporary AWS resources created for this exercise must be destroyed after both applications have been demonstrated and evidence collected.
