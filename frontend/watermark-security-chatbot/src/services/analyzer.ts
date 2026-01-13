import { AccessLog, ErrorLog, Threat, PerformanceIssue, Anomaly } from '../types';

export class LogAnalyzer {
    private accessLogs: AccessLog[];
    private errorLogs: ErrorLog[];

    constructor(accessLogs: AccessLog[], errorLogs: ErrorLog[]) {
        this.accessLogs = accessLogs;
        this.errorLogs = errorLogs;
    }

    public detectSecurityThreats(): Threat[] {
        const threats: Threat[] = [];

        const failedLogins = this.accessLogs.filter(log => log.statusCode === 401);
        const ipFailures = this.groupByIp(failedLogins);

        for (const [ip, count] of Object.entries(ipFailures)) {
            if (count >= 3) {
                threats.push({
                    severity: 'HIGH',
                    type: 'Brute Force Attack',
                    details: `${count} failed login attempts from IP ${ip}`,
                    recommendation: `Block IP ${ip} and enable rate limiting`
                });
            }
        }

        const sqlPatterns = this.accessLogs.filter(log =>
            /sqlmap|curl/i.test(log.userAgent)
        );

        sqlPatterns.forEach(log => {
            threats.push({
                severity: 'MEDIUM',
                type: 'SQL Injection Attempt',
                details: `Suspicious tool detected: ${log.userAgent} from ${log.ipAddress}`,
                recommendation: 'Review WAF rules and input sanitization'
            });
        });

        const botTraffic = this.accessLogs.filter(log =>
            /bot|python|curl/i.test(log.userAgent)
        );

        if (botTraffic.length > 0) {
            threats.push({
                severity: 'LOW',
                type: 'Automated Bot Activity',
                details: `${botTraffic.length} requests from automated tools`,
                recommendation: 'Implement CAPTCHA on sensitive endpoints'
            });
        }

        return threats;
    }

    public analyzeErrors(): any[] {
        const errors: any[] = [];

        const serverErrors = this.accessLogs.filter(log => log.statusCode >= 500);
        const notFoundErrors = this.accessLogs.filter(log => log.statusCode === 404);

        serverErrors.forEach(endpoint => {
            const count = serverErrors.filter(log => log.endpoint === endpoint.endpoint).length;
            errors.push({
                severity: 'HIGH',
                errorType: '500 Internal Server Error',
                endpoint: endpoint.endpoint,
                count: count,
                recommendation: 'Check PHP error logs for specific cause'
            });
        });

        if (notFoundErrors.length > 0) {
            errors.push({
                severity: 'MEDIUM',
                errorType: '404 Not Found',
                count: notFoundErrors.length,
                recommendation: 'Fix broken links or implement proper routing'
            });
        }

        return errors;
    }

    public detectPerformanceIssues(): PerformanceIssue[] {
        const issues: PerformanceIssue[] = [];
        const slowRequests = this.accessLogs.filter(log => log.responseTimeMs > 1000);

        slowRequests.forEach(endpoint => {
            const avgTime = this.calculateAverageResponseTime(endpoint.endpoint);
            const maxTime = Math.max(...slowRequests.map(log => log.responseTimeMs));

            issues.push({
                severity: maxTime > 3000 ? 'HIGH' : 'MEDIUM',
                endpoint: endpoint.endpoint,
                avgResponseTime: `${avgTime}ms`,
                peakResponseTime: `${maxTime}ms`,
                optimization: 'Add database indexing or implement caching'
            });
        });

        return issues;
    }

    public detectAnomalies(): Anomaly[] {
        const anomalies: Anomaly[] = [];
        const criticalErrors = this.errorLogs.filter(log => log.severityScore >= 8);

        criticalErrors.forEach(error => {
            anomalies.push({
                type: error.errorCode,
                severity: 'CRITICAL',
                message: error.errorMessage,
                timestamp: error.timestamp
            });
        });

        const agentKills = this.errorLogs.filter(log => log.errorCode === 'AGENT_KILL');
        if (agentKills.length > 0) {
            anomalies.push({
                type: 'Suspicious Agent Activity',
                severity: 'HIGH',
                message: `${agentKills.length} agent termination attempts detected`,
                timestamp: 'Various'
            });
        }

        return anomalies;
    }

    private groupByIp(logs: any[]): Record<string, number> {
        return logs.reduce((acc, log) => {
            acc[log.ipAddress] = (acc[log.ipAddress] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);
    }

    private calculateAverageResponseTime(endpoint: string): number {
        const endpointLogs = this.accessLogs.filter(log => log.endpoint === endpoint);
        const totalResponseTime = endpointLogs.reduce((sum, log) => sum + log.responseTimeMs, 0);
        return totalResponseTime / endpointLogs.length;
    }
}