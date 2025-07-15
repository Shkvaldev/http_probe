import argparse
import asyncio
from datetime import datetime

from logger import setup_logging
setup_logging()
import logging

from profiler import Profiler
from utils import parse_hosts, parse_hosts_file, make_test

async def display_progress(total_count: int, progress_queue: asyncio.Queue):
    """Displays current progress"""
    processed = 0
    while processed < total_count:
        processed_count = 0
        try:
            while processed_count < 1:
                await asyncio.sleep(0.5)
                while not progress_queue.empty():
                    await progress_queue.get()
                    processed += 1
                    processed_count += 1
        except asyncio.CancelledError:
            break

        logging.info(f"Прогресс: {processed}/{total_count} ({(processed / total_count) * 100:.2f}%)")

async def main() -> None:
    parser = argparse.ArgumentParser(
                    prog='http_probe',
                    description='CLI utility for checking the availability of HTTP servers')
    parser.add_argument('-F', '--file', type=str, help='file with hosts')
    parser.add_argument('-H', '--hosts', type=str, help='hosts (divided using ",")')
    parser.add_argument('-C', '--count', default=1, type=int, help='amount of requests per host (default, 1)')
    parser.add_argument('-O', '--output', type=str, help='output file with results (in HTML)')

    args = parser.parse_args()

    if args.file:
        try:
            hosts = parse_hosts_file(args.file)
        except Exception as e:
            logging.error(f"Failed to get URLs from file: {e}")
            exit(-1)
    elif args.hosts:
        try:
            hosts = parse_hosts(args.hosts)
        except Exception as e:
            logging.error(f"Failed to get URLs from command: {e}")
            exit(-1)
    else:
        logging.error("Not found any hosts - pass them via -F or -H argument")
        exit(-1)

    if not hosts:
        logging.error("Not found any URL - ensure, that URLs, passed via -F or -H, are valid!")
        exit(-1)

    # Making storage for tests results
    profiler = Profiler()
    # Making tasks
    tasks = []
    queue = asyncio.Queue()
    total_attempts = args.count * len(hosts)
    for i, host in enumerate(hosts):
        for attempt in range(1, args.count + 1):
            task = asyncio.create_task(make_test(
                                            url=host,
                                            queue=queue,
                                            profiler=profiler,
                                            timeout=5))
            tasks.append(task)
    tasks.append(display_progress(total_attempts, queue))
    
    # Running tests
    await asyncio.gather(*tasks)
    
    # Generating report
    result = await profiler.generate_report()

    # Printing results
    print("#"*10 + " RESULTS " + "#"*10)
    for url, data in result.items():
        print(f"""[ {url} ]:
        \t- Success: {data['success']}
        \t- Failed: {data['failed']}
        \t- Errors: {data['errors']}
        \t- Min: {data['min']:.03f} sec.
        \t- Max: {data['max']:.03f} sec.
        \t- Avg: {data['avg']:.03f} sec.
        """)

    # Writing report to file (as HTML)
    if args.output:
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_data = ""
        chart_data = ""
        for url, data in result.items():
            report_data += f"""<tr>
                <td>{url}</td>
                <td>{data['success']}</td>
                <td>{data['failed']}</td>
                <td>{data['errors']}</td>
                <td>{data['min']:.03f}</td>
                <td>{data['max']:.03f}</td>
                <td>{data['avg']:.03f}</td>
            </tr>
            """
        
        # Filling in template
        try:
            with open("report_template.html", "r") as template:
                html_data = template.read()
            
            html_data = html_data.replace("%%report_date%%", report_date)
            html_data = html_data.replace("%%report_data%%", report_data)
        except Exception as e:
            logging.error(f"Failed to generate report in HTML: {e}")
            exit(-1)
        
        try:
            with open(args.output, "w") as output_file:
                output_file.write(html_data)
        except Exception as e:
            logging.error(f"Failed to save results to file `{args.output}`: {e}")
            exit(-1)

        logging.info("HTML report generated successfully")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Force shutdown by user ...")