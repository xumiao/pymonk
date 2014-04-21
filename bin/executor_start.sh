cp monk/roles/executor.yml executor.yml
cp monk/roles/executor_service.py executor_service.rpy
twistd web --path=. --ignore-ext=py --port 80
