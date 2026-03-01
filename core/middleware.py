from django.shortcuts import redirect

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Only protect certain paths
        protected_prefixes = {
            '/hr/': 'HR',
            '/employee/': 'EMPLOYEE',
            '/client/': 'CLIENT',
        }

        required_role = None
        for prefix, role in protected_prefixes.items():
            if path.startswith(prefix):
                required_role = role
                break

        if required_role:
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Check user role
            has_role = request.user.groups.filter(name=required_role).exists()
            if not has_role:
                # Redirect to appropriate dashboard based on actual roles
                if request.user.groups.filter(name="HR").exists():
                    return redirect("hr:dashboard")
                elif request.user.groups.filter(name="CLIENT").exists():
                    return redirect("core:client_dashboard")
                elif request.user.groups.filter(name="EMPLOYEE").exists():
                    return redirect("employee:employee_dashboard")
                else:
                    return redirect("login")

        response = self.get_response(request)
        return response
