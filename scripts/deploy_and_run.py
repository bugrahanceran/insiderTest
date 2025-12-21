import argparse
import subprocess
import time
import sys
import os
import re

# For colored outputs
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def run_command(command, check=True):
    """Executes terminal commands and returns the output."""
    try:
        result = subprocess.run(
            command,
            check=check,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Colors.FAIL}[ERROR] Command failed: {command}{Colors.ENDC}")
        print(f"{Colors.FAIL}Error Details: {e.stderr}{Colors.ENDC}")
        if check:
            sys.exit(1)
        return None

def update_node_count(replicas):
    """Updates the replica count in chrome-node.yaml file."""
    print(f"{Colors.OKBLUE}[INFO] Setting Chrome Node count to {replicas}...{Colors.ENDC}")
    
    file_path = 'k8s/chrome-node.yaml'
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Find and replace the 'replicas: X' line using regex
    new_content = re.sub(r'replicas:\s*\d+', f'replicas: {replicas}', content)
    
    with open(file_path, 'w') as file:
        file.write(new_content)

def check_pods_ready(label_selector, timeout=120):
    """Waits for pods to reach the Ready state."""
    print(f"{Colors.OKBLUE}[INFO] Waiting for pods to be ready ({label_selector})...{Colors.ENDC}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check pod statuses
        cmd = f"kubectl get pods -l {label_selector} -o jsonpath='{{.items[*].status.phase}}'"
        output = run_command(cmd, check=False)
        
        if output:
            phases = output.split()
            # If all are 'Running' and the count matches the expectation (basic check)
            if all(p == 'Running' for p in phases) and len(phases) > 0:
                # Deeper check: Ready condition
                cmd_ready = f"kubectl wait --for=condition=ready pod -l {label_selector} --timeout=5s"
                res = run_command(cmd_ready, check=False)
                if res:
                    print(f"{Colors.OKGREEN}[OK] All {label_selector} pods are ready!{Colors.ENDC}")
                    return True
        
        time.sleep(5)
        print(f"Waiting for pods... ({int(time.time() - start_time)}s)")
    
    print(f"{Colors.FAIL}[TIMEOUT] Pods could not be ready within {timeout} seconds.{Colors.ENDC}")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Kubernetes Selenium Test Runner')
    parser.add_argument('--nodecount', type=int, required=True, help='Chrome Node count (1-5)')
    args = parser.parse_args()

    # Validation
    if not (1 <= args.nodecount <= 5):
        print(f"{Colors.FAIL}Error: nodecount must be between 1 and 5.{Colors.ENDC}")
        sys.exit(1)

    print(f"{Colors.HEADER}--- Deployment Starting ---{Colors.ENDC}")

    # 1. Update Chrome Node count
    update_node_count(args.nodecount)

    # 2. Clean up previous deployments (Clean State)
    print(f"{Colors.WARNING}[INFO] Cleaning up old resources...{Colors.ENDC}")
    run_command("kubectl delete deployment test-controller-deployment --ignore-not-found", check=False)
    run_command("kubectl delete deployment chrome-node-deployment --ignore-not-found", check=False)
    run_command("kubectl delete service chrome-node-service --ignore-not-found", check=False)
    time.sleep(5) # Short wait for Kubernetes to delete

    # 3. Deploy Chrome Nodes
    print(f"{Colors.OKBLUE}[INFO] Deploying Chrome Nodes...{Colors.ENDC}")
    run_command("kubectl apply -f k8s/chrome-node.yaml")

    # 4. Wait for Chrome Nodes to be Ready
    check_pods_ready("app=chrome-node")

    # 5. Deploy Test Controller
    print(f"{Colors.OKBLUE}[INFO] Deploying Test Controller...{Colors.ENDC}")
    run_command("kubectl apply -f k8s/test-controller.yaml")
    check_pods_ready("app=test-controller")

    # 6. Monitor Test Controller Logs
    print(f"{Colors.HEADER}--- Monitoring Test Logs ---{Colors.ENDC}")
    
    # Find the controller pod name
    time.sleep(3) # Short wait for the pod to be created
    pod_name_cmd = "kubectl get pods -l app=test-controller -o jsonpath='{.items[0].metadata.name}'"
    pod_name = run_command(pod_name_cmd)
    
    if pod_name:
        print(f"Controller Pod: {pod_name}")
        # Stream logs (-f)
        try:
            subprocess.run(f"kubectl logs -f {pod_name}", shell=True)
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Log monitoring stopped.{Colors.ENDC}")
        finally:
            # The test is finished (successful or failed), we no longer need the pod.
            # Let's delete it before it goes into CrashLoopBackOff.
            print(f"\n{Colors.WARNING}[CLEANUP] Test completed. Deleting the controller deployment...{Colors.ENDC}")
            run_command("kubectl delete deployment test-controller-deployment")
            print(f"{Colors.OKGREEN}[OK] Cleanup completed. CrashLoopBackOff prevented.{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}[ERROR] Controller pod not found!{Colors.ENDC}")

if __name__ == "__main__":
    main()