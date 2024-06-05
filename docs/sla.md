# Service Level Agreement (SLA)

This document outlines Datacoves' responsibility with regards to outages and other issues with the Datacoves platform.

## Support

Datacoves monitors their platforms continually, 24 hours a day, 7 days a week.  Support is based on severity level of the issue, with 1 being the highest and 3 being the lowest:

| Severity Level | Level of Effort | Initial response | Status Updates |
| :--------------: | --------------- | ---------------- | -------------- |
| 1 | Commercially reasonable efforts, during normal business hours. | Immediate and in no event to exceed 24 hours. | Every 1 Business Day or sooner via email or Slack communication |
| 2 | Commercially reasonable efforts, during normal business hours. | 24 hours |Every 1 Business Day or sooner via email or Slack communication |
| 3 | Commercially reasonable efforts, during normal business hours | 3 Business Days | Every 2 Business Days prior to a work around and every 5 business days thereafter |

Business hours are defined as between 8 AM Eastern US time and 8 PM Eastern US time.  Typically, we are able to respond to issues at all levels within an hour or less during Business Hours.  Support is provided remotely by English-speaking resources via customer-specific Slack channels or via email to support@datacoves.com.

### Severity Levels

Our severity levels are defined as follows:

| Severity Level | Definition |
| :------------: | ---------- |
| 1 | Any error that renders the platform or any major portion of it inoperative, or majorly impacts the customer's use of the platform in a production environment.  For instance, if the platform has a total loss of service, frequent instabilities, or a loss of ability to communicate as intended. |
| 2 | Any error that impairs the use of one or more features of the platform, but not a major portion of it, unusable in a production environment.  This also covers errors in non-production environments that would be a level 1 error in production. |
| 3 | Any error that has a minimal impact on the performance or operation of the platform, and most errors in non-production environments that are not severe enough to fall under level 2. |

### Types of Issues

We provide support for the following types of issues:

| Type | Example | Price |
| :--: | ------- | ----- |
| Bug | User logs into Datacoves and can't get to the dbt environment due to a bug with the platform. | Included |
| System Integration (Non-Datacoves issues) | Github is updated and users cannot pull or push changes, requiring a specific fix to support that  integration. | 12 incidents included; additional would fall under professional services |
| Enhancements | Customer has a CI/CD process that impacted by a change to dbt Core | Not Included - Professional Services |

Datacoves strives to be helpful to its customers and we will do our best to provide assistance with most issues.

## Notification of Outages or other System Events

Datacoves maintains a status page at the following URL: [https://status.datacoves.com/](https://status.datacoves.com/)

We are pro-active in our approach to support and we notify all applicable customer Slack support channels when there is a notification regarding an upgrade, outage, or other items that may impact a customer's usage of the system.

## Requesting Support

Customers may request support via their private Slack channel which is set up as part of the onboarding process.  Support may also be requested via email at: support@datacoves.com

When notifying Datacoves about a bug, please provide the following pieces of information:

 * The time and date the error occurred, if available
 * Which environment the occurred on, if applicable
 * A description of the problem, including what is impacted by the error
 * The severity of the error (Something minor; cosmetic, easily worked around error, etc.  Or something major; cannot function due to error)

Once notified, Datacoves will open an internal ticket and work on the issue according to the charts in the above section.

## Availability

Datacoves' availability and functionality is dependent upon outside factors, some of which are outside of Datacoves' control.  For instance, GitHub integrations will not function if GitHub is down.  Such instances are completely outside of Datacoves' control and therefore we cannot be responsible for outages due to those third party services.

We use AWS and Azure for hosting customer clusters.  Generally speaking, these services have no down time; down times are typically due to upgrades and maintenance work, which Datacoves notifies its customers of in advance and performs on an agreed upon schedule.

For services run by Datacoves, we assert they will be available for 99.9% of the total number of minutes that make up a given month.

### Exceptions to Availability

The Availability SLA does not apply to the following events:

 * Scheduled, announced maintenance or emergency maintenance
 * An act or omission of our client, or client's vendors/agents, client's internal or third party services, or any occurrence due to client's maintenance
 * Suspension of service due to non-payment

### Credits

If we fail to meet our Availability SLA for a given month, then Datacoves shall, upon our client's written request to be submitted within 30 calendar days of the unavailability, apply a credit to the client account on the following schedule:

| Availability in a Month | Credit Amount (Percent of Monthly Fees) |
| ----------------------- | --------------------------------------- |
| Less than 99.8%         | 1% |
| Less than 99.7%         | 2% |
| Less than 99.6%         | 3% |
| Less than 99.5%         | 4% |
| Less than 99.4%         | 5% |

After confirming the validity of the request, Datacoves will issue the credit in the next month after the SLA failure.  If the SLA failure was in the last month of a client's contract and they choose not to renew, the amount will be provided as a refund.  A maximum of 5% credit/refund will be provided.

