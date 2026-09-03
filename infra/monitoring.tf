resource "aws_cloudwatch_metric_alarm" "sqs_backlog" {
  alarm_name        = "${var.project_name}-sqs-backlog"
  alarm_description = "Alerts when the SQS queue accumulates too many unprocessed messages"

  namespace   = "AWS/SQS"
  metric_name = "ApproximateNumberOfMessagesVisible"
  dimensions = {
    QueueName = aws_sqs_queue.main.name
  }

  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 100
  comparison_operator = "GreaterThanThreshold"
  alarm_actions       = [aws_sns_topic.alerts.arn]

}


resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name        = "${var.project_name}-ec2-cpu-high"
  alarm_description = "Alert when the CPU is greater than 80 percent"

  namespace   = "AWS/EC2"
  metric_name = "CPUUtilization"

  dimensions = {
    InstanceId = aws_instance.app.id
  }

  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  alarm_actions       = [aws_sns_topic.alerts.arn]

}


resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
