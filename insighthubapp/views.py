from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserSignUpForm, UserLoginForm, DatasetForm, DashboardForm, CommentForm, SelectedColumnsForm
from .models import UserProfile, Roles, Dashboards, Datasets, Charts, Chart_Types, Social_Like, Social_Comment, Dataset_Columns, Selected_Columns
import csv, json
from django.utils.html import escape
from django.http import JsonResponse
from django.db.models import Count
import os
from django.conf import settings


def index(request):
    features = [
        {
            'title': 'Upload & Create Dashboards',
            'desc': 'Start by uploading a CSV file to generate a dynamic dashboard instantly. No complex setup—just drag, drop, and explore.',
            'image': 'insighthubapp/images/f1.png',
            'reverse': False,
        },
        {
            'title': 'Real-time Spreadsheet & Chart Sync',
            'desc': 'Modify data directly in the online spreadsheet and see immediate updates in the visual charts. Stay in control of your data.',
            'image': 'insighthubapp/images/f2.png',
            'reverse': True,
        },
        {
            'title': 'Effortless Chart Conversion',
            'desc': 'Switch between bar charts and line charts with a single click, ensuring the best data representation for your needs.',
            'image': 'insighthubapp/images/f3.png',
            'reverse': False,
        },
        {
            'title': 'Share with a QR Code',
            'desc': 'Easily share dashboards with your team or audience using a QR code. No logins or downloads—just instant access.',
            'image': 'insighthubapp/images/f4.png',
            'reverse': True,
        },
        {
            'title': 'Explore & Interact',
            'desc': 'Browse other users’ dashboards, engage with their insights, and be part of a data-driven community.',
            'image': 'insighthubapp/images/f5.png',
            'reverse': False,
        },
    ]
    return render(request, "index.html", {"features": features, "show_header": True, "show_footer": True})


def signup(request):
    if request.method == "POST":
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("projects")
        else:
            print(form.errors)
    else:
        form = UserSignUpForm()
    return render(request, "signup.html", {"form": form, "show_header": False, "show_footer": False})


def login(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data.get("username"),
                password=form.cleaned_data.get("password")
            )
            if user is not None:
                auth_login(request, user)
                return JsonResponse({"success": True, "redirect_url": "/insighthubproject/projects/"})
            else:
                return JsonResponse({"success": False, "error": "Invalid credentials."})
        else:
            return JsonResponse({"success": False, "error": form.errors.as_json()})
    
    form = UserLoginForm()
    return render(request, "login.html", {
        "form": form,
        "show_header": False,
        "show_footer": False
    })


def logout(request):
    auth_logout(request)
    return redirect("login")


@login_required
def projects(request):
    if request.method == "GET":
        dashboards = Dashboards.objects.filter(user=request.user)

        chart_previews = []

        for d in dashboards:
            chart_data = []
            chart_type = "bar"
            axis = {}

            if d.chart and d.chart.dataset and d.chart.dataset.file_path:
                try:
                    with d.chart.dataset.file_path.open(mode='r') as f:
                        reader = csv.reader(f)
                        chart_data = list(reader)
                except Exception as e:
                    print(f"Failed to read CSV for dashboard {d.id}: {e}")
                    chart_data = []

                selected_columns = Selected_Columns.objects.filter(chart=d.chart)
                for sel in selected_columns:
                    axis[sel.axis_type] = sel.column.column_name

            if d.chart and d.chart.chart_type and d.chart.chart_type.chart_type:
                if d.chart.chart_type.chart_type == "Bar Chart":
                    chart_type = "bar"
                elif d.chart.chart_type.chart_type == "Line Chart":
                    chart_type = "line"

            chart_previews.append({
                "id": d.id,
                "type": chart_type,
                "data": chart_data,
                "axis": axis,
            })

            
        return render(request, "projects.html", {
            "projects": dashboards,
            "chart_previews_json": json.dumps(chart_previews),
            "show_header": True,
            "show_footer": True
        })
    return redirect("index")


@login_required
def create_dashboard(request):
    if request.method == "POST":
        dashboard = Dashboards.objects.create(
            user=request.user,
            name="Untitled Dashboard",
            description="",
            status=True,
        )
        return redirect("dashboard", pk=dashboard.id)
    return redirect("projects")


@login_required
def dashboard(request, pk):
    dashboard = get_object_or_404(Dashboards, pk=pk, user=request.user)
    dataset = Datasets.objects.filter(user=request.user, dashboard=dashboard).first()
    selected_columns = Selected_Columns.objects.filter(chart=dashboard.chart) if dashboard.chart else None

    csv_data = []
    axis = []
    axis_letter = []

    if (selected_columns):
        for sel in selected_columns:
            axis.append({sel.axis_type: sel.column.column_name})

    if dataset and dataset.file_path:
        with dataset.file_path.open(mode='r') as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            colname_to_letter = {col_name: chr(ord('A') + idx) for idx, col_name in enumerate(csv_data[0])}
    else:
        colname_to_letter = {}

    if selected_columns:
        for sel in selected_columns:
            col_letter = colname_to_letter.get(sel.column.column_name, sel.column.column_name)
            axis_letter.append({sel.axis_type: col_letter})


    if request.method == "POST":
        dashboard_form = DashboardForm(request.POST, instance=dashboard)
        dataset_form = DatasetForm(request.POST, request.FILES, instance=dataset, user=request.user, dashboard=dashboard)
        selected_columns_form = SelectedColumnsForm(request.POST)

        if request.headers.get("X-Action") == "data":
            try:
                # Accept updated CSV content in request body
                csv_string = request.body.decode('utf-8')
                csv_rows = list(csv.reader(csv_string.splitlines()))
                if dataset:
                    with dataset.file_path.open(mode='w') as f:
                        writer = csv.writer(f)
                        writer.writerows(csv_rows)
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'No dataset found.'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
            
        action = request.POST.get("action")
        if not action and "file_path-clear" in request.POST:
            action = "data"

        if action == "chart":
            if dashboard_form.is_valid() and dataset_form.is_valid():
                dashboard = dashboard_form.save(commit=False)
                dashboard.user = request.user
                dashboard.save()

                new_dataset = dataset_form.save(commit=False)
                new_dataset.user = request.user
                new_dataset.dashboard = dashboard
                new_dataset.save()

                # Extract header and create Dataset_Columns
                if (new_dataset.file_path):
                    with new_dataset.file_path.open(mode='r') as f:
                        reader = csv.reader(f)
                        header = next(reader)
                        if header:
                            for idx, col_name in enumerate(header):
                                Dataset_Columns.objects.create(
                                    column_name=col_name,
                                    data_type="string",
                                    dataset=new_dataset
                                )

                chart_type = dashboard_form.cleaned_data.get("chart_type")
                if dashboard.chart:
                    chart = dashboard.chart
                    chart.chart_type = chart_type
                    chart.dataset = new_dataset
                    chart.save()
                else:
                    chart = Charts.objects.create(
                        dashboard=dashboard,
                        dataset=new_dataset,
                        chart_type=chart_type
                    )
                    dashboard.chart = chart
                    dashboard.save()

                status = dashboard_form.cleaned_data.get("status")
                dashboard.status = True if status == "True" else False
                dashboard.save()

                return redirect("dashboard", pk=dashboard.pk)
            
        elif action == "data":
            if dashboard_form.is_valid():
                dashboard = dashboard_form.save(commit=False)
                dashboard.user = request.user
                dashboard.save()


            # if dataset_form.is_valid():
            #     new_dataset = dataset_form.save()
            #     new_dataset.user = request.user
            #     new_dataset.dashboard = dashboard
            #     new_dataset.save()

            #     # Extract header and create Dataset_Columns
            #     with new_dataset.file_path.open(mode='r') as f:
            #         reader = csv.reader(f)
            #         header = next(reader)
            #         if header:
            #             for idx, col_name in enumerate(header):
            #                 Dataset_Columns.objects.create(
            #                     column_name=col_name,
            #                     data_type="string",
            #                     dataset=new_dataset
            #                 )


            if dataset_form.is_valid():
                new_dataset = dataset_form.save()
                new_dataset.user = request.user
                new_dataset.dashboard = dashboard
                new_dataset.save()
                header = []

                # Only extract header and create Dataset_Columns if file exists
                if new_dataset.file_path:
                    with new_dataset.file_path.open(mode='r') as f:
                        reader = csv.reader(f)
                        header = next(reader)
                        if header:
                            for idx, col_name in enumerate(header):
                                Dataset_Columns.objects.create(
                                    column_name=col_name,
                                    data_type="string",
                                    dataset=new_dataset
                                )
                else:
                    # Optionally, you can delete Dataset_Columns if file is cleared
                    Dataset_Columns.objects.filter(dataset=new_dataset) .delete()
            
            if selected_columns_form.is_valid():
                selected_columns = selected_columns_form.save(commit=False)
                x_letter = selected_columns_form.cleaned_data['x_axis']
                y_letter = selected_columns_form.cleaned_data['y_axis']
                category_letter = selected_columns_form.cleaned_data['category']
                series_letter = selected_columns_form.cleaned_data['series']

                x_index = col_letter_to_index(x_letter)
                y_index = col_letter_to_index(y_letter)
                category_index = col_letter_to_index(category_letter)
                series_index = col_letter_to_index(series_letter)

                if dataset_form.is_valid():
                    new_dataset = dataset_form.save()
                    new_dataset.user = request.user
                    new_dataset.dashboard = dashboard
                    new_dataset.save()

                    if new_dataset.file_path:
                        with new_dataset.file_path.open(mode='r') as f:
                            reader = csv.reader(f)
                            header = next(reader, [])

                    if 0 <= x_index < len(header):
                        x_col_name = header[x_index]
                        x_col = Dataset_Columns.objects.filter(dataset=dataset, column_name=x_col_name).first()
                        if x_col:
                            Selected_Columns.objects.update_or_create(
                                chart=dashboard.chart,
                                axis_type='x',
                                defaults={'column': x_col}
                            )

                    if 0 <= y_index < len(header):
                        y_col_name = header[y_index]
                        y_col = Dataset_Columns.objects.filter(dataset=dataset, column_name=y_col_name).first()
                        if y_col:
                            Selected_Columns.objects.update_or_create(
                                chart=dashboard.chart,
                                axis_type='y',
                                defaults={'column': y_col}
                            )

                    if 0 <= category_index < len(header):
                        category_col_name = header[category_index]
                        category_col = Dataset_Columns.objects.filter(dataset=dataset, column_name=category_col_name).first()
                        if category_col:
                            Selected_Columns.objects.update_or_create(
                                chart=dashboard.chart,
                                axis_type='category',
                                defaults={'column': category_col}
                            )
                    
                    if 0 <= series_index < len(header):
                        series_col_name = header[series_index]
                        series_col = Dataset_Columns.objects.filter(dataset=dataset, column_name=series_col_name).first()
                        if series_col:
                            Selected_Columns.objects.update_or_create(
                                chart=dashboard.chart,
                                axis_type='series',
                                defaults={'column': series_col}
                            )
                selected_columns_form.save()
                return redirect("dashboard", pk=dashboard.pk)
    else:
        dataset_form = DatasetForm(instance=dataset)
        if dataset_form.is_valid():
            print("post dataset_form")
            new_dataset = dataset_form.save(user=request.user, dashboard=dashboard)
        selected_columns_qs = Selected_Columns.objects.filter(chart=dashboard.chart) if dashboard.chart else []
        initial = {
            'chart_type': dashboard.chart.chart_type if dashboard.chart else None,
        }
        dashboard_form = DashboardForm(instance=dashboard, initial=initial)
        for sel in selected_columns_qs:
            col_letter = colname_to_letter.get(sel.column.column_name, sel.column.column_name)
            if sel.axis_type == 'x':
                initial['x_axis'] = col_letter
            elif sel.axis_type == 'y':
                initial['y_axis'] = col_letter
            elif sel.axis_type == 'category':
                initial['category'] = col_letter
            elif sel.axis_type == 'series':
                initial['series'] = col_letter
        selected_columns_form = SelectedColumnsForm(initial=initial)

    return render(request, "dashboard.html", {
        "dashboard_form": dashboard_form,
        "dataset_form": dataset_form,
        "selected_columns_form": selected_columns_form,
        "dashboard": dashboard,
        "csv_data": json.dumps(csv_data),
        "axis": json.dumps(axis),
        "axis_letter": json.dumps(axis_letter),
        "show_header": True,
        "show_footer": True
    })
    
@login_required
def delete_dashboard(request, pk):
    dashboard = get_object_or_404(Dashboards, pk=pk)
    if request.method == "POST":
        dashboard.delete()
        return redirect("projects")
        
    return render(request, "projects.html", {"dashboard": dashboard})


@login_required
def publicProjects(request):
    if request.method == "GET":
        publicProjects = Dashboards.objects.filter(status=0).annotate(
            like_count=Count('social_like'),
            comment_count=Count('social_comment')
        )  # join social_like and dashboard tables
        chart_previews = []
        for pd in publicProjects:
            chart_data = []
            chart_type = "bar"
            axis = {}

            if pd.chart and pd.chart.dataset and pd.chart.dataset.file_path:
                try:
                    with pd.chart.dataset.file_path.open(mode='r') as f:
                        reader = csv.reader(f)
                        chart_data = list(reader)
                except Exception as e:
                    print(f"Failed to read CSV for dashboard {pd.id}: {e}")
                    chart_data = []

            selected_columns = Selected_Columns.objects.filter(chart=pd.chart)
            for sel in selected_columns:
                axis[sel.axis_type] = sel.column.column_name

            if pd.chart and pd.chart.chart_type and pd.chart.chart_type.chart_type:
                if pd.chart.chart_type.chart_type == "Bar Chart":
                    chart_type = "bar"
                elif pd.chart.chart_type.chart_type == "Line Chart":
                    chart_type = "line"
            chart_previews.append({
                "id": pd.id,
                "type": chart_type,
                "data": chart_data,
                "axis": axis,
                "like_count": pd.like_count,
                "comment_count": pd.comment_count,
            })

        return render(request, "publicProjects.html", {
            "projects": publicProjects,
            "chart_preview_json": json.dumps(chart_previews),
            "show_header": True,
            "show_footer": True
        })
    return redirect("index")


def publicDashboard(request, pk):
    dashboard = get_object_or_404(Dashboards, pk=pk)
    chart = dashboard.chart
    dataset = chart.dataset if chart else None
    chart_data = []
    chart_type = "bar"
    axis = {}

    if dataset and dataset.file_path:
        file_path = os.path.join(settings.MEDIA_ROOT, dataset.file_path.name)
        try:
            with open(file_path, mode='r') as f:
                reader = csv.reader(f)
                chart_data = list(reader)
        except Exception as e:
            print(f"Failed to read CSV for dashboard {dashboard.id}: {e}")
            chart_data = []

    if chart:
        selected_columns = Selected_Columns.objects.filter(chart=chart)
        for sel in selected_columns:
            axis[sel.axis_type] = sel.column.column_name

    if chart.chart_type.chart_type == "Bar Chart":
        chart_type = "bar"
    elif chart.chart_type.chart_type == "Line Chart":
        chart_type = "line"

    comments = Social_Comment.objects.filter(dashboard=dashboard)
    like = Social_Like.objects.filter(dashboard=dashboard, user=request.user).exists()
    like_count = Social_Like.objects.filter(dashboard=dashboard).count()

    form = CommentForm()

    return render(request, "publicDashboard.html", {
        "publicDashboard": dashboard,
        "comment_form": form,
        "social_comments": comments,
        "social_likes": like_count,
        "like": like,
        "chart_data": json.dumps(chart_data),
        "chart_type": chart_type,
        "axis": json.dumps(axis),
        "show_header": True,
        "show_footer": True,
    })


@login_required
def create_publicDashboard_comment(request, pk):
    dashboard = get_object_or_404(Dashboards, pk=pk)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.dashboard = dashboard
            comment.save()
            return redirect('publicDashboard', pk=pk)
    else:
        form = CommentForm()

    return redirect('publicDashboard', pk=pk)


@login_required
def create_publicDashboard_like(request, pk):
    if request.method == 'POST':
        dashboard = get_object_or_404(Dashboards, pk=pk)
        user = request.user

        existing_like = Social_Like.objects.filter(user=user, dashboard=dashboard)

        if existing_like.exists():
            # delete
            existing_like.delete()
            like = False
        else:
            # add
            Social_Like.objects.create(user=user, dashboard=dashboard)
            like = True

        like_count = Social_Like.objects.filter(dashboard=dashboard).count()
        return JsonResponse({'liked': like, 'like_count': like_count})


# Convert columns letter to zero-based index
def col_letter_to_index(letter):
    result = 0
    for char in letter.upper():
        result = result * 26 + (ord(char) - ord('A') + 1)

    return result - 1